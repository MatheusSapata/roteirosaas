import pytest

from app.services.url_import import (
    MIN_TRIP_CARDS,
    UrlImportError,
    _candidate_images,
    _ensure_public_http_url,
    _extract,
    classify_page,
    normalize_url,
)
from bs4 import BeautifulSoup


def test_ensure_public_http_url_rejects_non_http_scheme():
    with pytest.raises(UrlImportError):
        _ensure_public_http_url("ftp://exemplo.com/arquivo")


def test_ensure_public_http_url_rejects_localhost():
    with pytest.raises(UrlImportError):
        _ensure_public_http_url("http://localhost:8000/admin")


def test_ensure_public_http_url_rejects_loopback_ip():
    with pytest.raises(UrlImportError):
        _ensure_public_http_url("http://127.0.0.1/")


def test_ensure_public_http_url_rejects_link_local_metadata_ip():
    # Endereço de metadados de nuvem (AWS/GCP/Azure): alvo clássico de SSRF.
    with pytest.raises(UrlImportError):
        _ensure_public_http_url("http://169.254.169.254/latest/meta-data/")


def test_ensure_public_http_url_accepts_public_host(monkeypatch):
    # Sem depender de DNS real no ambiente de teste: só confere que um endereço
    # público (não privado/loopback/link-local) passa pela guarda.
    monkeypatch.setattr(
        "app.services.url_import.socket.getaddrinfo",
        lambda *_args, **_kwargs: [(2, 1, 6, "", ("93.184.216.34", 0))],
    )
    _ensure_public_http_url("https://exemplo.com.br/pacote-gramado")


HTML_SAMPLE = """
<html>
<head>
  <title>Pacote Gramado 5 dias</title>
  <meta property="og:title" content="Pacote Gramado 5 dias e 4 noites" />
  <meta property="og:image" content="/img/capa.jpg" />
</head>
<body>
  <nav><a href="/">Início</a></nav>
  <article>
    <h1>Pacote Gramado 5 dias e 4 noites</h1>
    <p>Viaje para a Serra Gaúcha com tudo incluso: hospedagem, café da manhã e passeios.</p>
    <p>Valor: R$ 2.490 por pessoa, em até 10x sem juros.</p>
    <img src="/img/hotel.jpg" width="800" />
    <img src="/img/icone.png" width="16" />
  </article>
  <footer>Direitos reservados</footer>
</body>
</html>
"""


def test_extract_reads_title_and_body_text():
    page = _extract(HTML_SAMPLE, "https://exemplo.com.br/pacote-gramado")
    assert page.title == "Pacote Gramado 5 dias e 4 noites"
    assert "Serra Gaúcha" in page.text
    assert "2.490" in page.text


def test_extract_fails_on_empty_page():
    with pytest.raises(UrlImportError):
        _extract("<html><body></body></html>", "https://exemplo.com.br/vazio")


def test_candidate_images_prefers_og_image_and_skips_small_icons():
    soup = BeautifulSoup(HTML_SAMPLE, "html.parser")
    images = _candidate_images(soup, "https://exemplo.com.br/pacote-gramado")
    assert images[0] == "https://exemplo.com.br/img/capa.jpg"
    assert "https://exemplo.com.br/img/hotel.jpg" in images
    assert not any(url.endswith("icone.png") for url in images)


# --- Classificação: página de uma viagem ou página central (home com várias viagens) ---

def _card(slug: str, title: str, price: str = "R$ 1.990,00") -> str:
    return f"""
    <article class="trip-card">
      <a href="/{slug}"><img src="/img/{slug}.jpg" width="600" /></a>
      <h3><a href="/{slug}">{title}</a></h3>
      <p class="price">A partir de {price} por pessoa</p>
      <a class="btn" href="/{slug}">Saiba mais</a>
      <a href="https://wa.me/5511999999999?text=Quero%20{slug}">Reservar pelo WhatsApp</a>
    </article>
    """


HOME_HTML = f"""
<html>
<head><title>Agência Exemplo | Viagens em grupo</title></head>
<body>
  <nav><a href="/">Início</a> <a href="/sobre">Sobre</a> <a href="/contato">Contato</a>
    <a href="https://instagram.com/agencia">Instagram</a></nav>
  <h1>Próximas saídas</h1>
  <section class="grid">
    {_card("viagens/gramado-inverno", "Gramado no inverno")}
    {_card("viagens/beto-carrero", "Beto Carrero World", "R$ 899")}
    {_card("viagens/foz-do-iguacu", "Foz do Iguaçu", "R$1.290,50")}
    {_card("viagens/campos-do-jordao", "Campos do Jordão")}
    {_card("viagens/porto-seguro", "Porto Seguro", "US$ 450")}
  </section>
  <footer><a href="/politica-de-privacidade">Privacidade</a></footer>
</body>
</html>
"""


def test_classify_home_with_trip_cards_as_central():
    result = classify_page(HOME_HTML, "https://agencia.com.br/")
    assert result.kind == "central"
    urls = [link.url for link in result.trip_links]
    assert urls == [
        "https://agencia.com.br/viagens/gramado-inverno",
        "https://agencia.com.br/viagens/beto-carrero",
        "https://agencia.com.br/viagens/foz-do-iguacu",
        "https://agencia.com.br/viagens/campos-do-jordao",
        "https://agencia.com.br/viagens/porto-seguro",
    ]
    gramado = result.trip_links[0]
    assert gramado.title == "Gramado no inverno"
    assert gramado.price == "R$ 1.990,00"
    assert "Gramado no inverno" in gramado.text
    # WhatsApp, rede social e menu nunca viram "viagem".
    assert not any("wa.me" in url or "instagram" in url or url.endswith("/sobre") for url in urls)


def test_classify_single_trip_page_as_specific():
    # Página de uma viagem só (preço único, sem cards levando para outros links).
    result = classify_page(HTML_SAMPLE, "https://exemplo.com.br/pacote-gramado")
    assert result.kind == "specific"
    assert result.trip_links == []


def test_classify_cards_without_price_by_card_buttons():
    cards = "".join(
        f'<div class="card"><img src="/i{n}.jpg"/><h2>Destino {n}</h2><p>Roteiro de 5 dias.</p>'
        f'<a href="/roteiros/destino-{n}">Ver roteiro</a></div>'
        for n in range(1, 6)
    )
    html = f"<html><body><h1>Roteiros</h1>{cards}<a href='/sobre'>Saiba mais sobre a agência</a></body></html>"
    result = classify_page(html, "https://agencia.com.br/roteiros")
    assert result.kind == "central"
    assert [link.title for link in result.trip_links] == [f"Destino {n}" for n in range(1, 6)]
    assert all(link.price == "" for link in result.trip_links)


def test_classify_trip_page_with_related_trips_carousel_stays_specific():
    # Página de uma viagem com o próprio roteiro dia a dia e um carrossel de "outras viagens":
    # os cards existem, mas o conteúdo principal é de uma viagem só.
    related = "".join(_card(f"viagens/outra-{n}", f"Outra viagem {n}") for n in range(1, 6))
    html = f"""
    <html><body>
      <h1>Pacote Gramado 5 dias</h1>
      <p>Valor: R$ 2.490 por pessoa.</p>
      <h2>Roteiro</h2>
      <p>Dia 1: Chegada e city tour.</p><p>Dia 2: Snowland.</p><p>Dia 3: Canela e Caracol.</p>
      <h2>Outras viagens</h2>{related}
    </body></html>
    """
    assert classify_page(html, "https://agencia.com.br/viagens/gramado").kind == "specific"


def test_classify_needs_minimum_distinct_links():
    # Três cards (abaixo do mínimo) e cards repetindo o mesmo link não fazem uma página central.
    few = "".join(_card(f"viagens/v{n}", f"Viagem {n}") for n in range(1, MIN_TRIP_CARDS))
    same = "".join(_card("viagens/unica", f"Data {n}") for n in range(1, 6))
    assert classify_page(f"<html><body>{few}</body></html>", "https://a.com/").kind == "specific"
    assert classify_page(f"<html><body>{same}</body></html>", "https://a.com/").kind == "specific"


def test_extract_central_page_keeps_trip_links():
    page = _extract(HOME_HTML, "https://agencia.com.br/")
    assert page.is_central
    assert len(page.trip_links) == 5


def test_normalize_url_ignores_scheme_www_fragment_and_trailing_slash():
    assert normalize_url("https://www.Agencia.com.br/viagens/gramado/#datas") == normalize_url(
        "http://agencia.com.br/viagens/gramado"
    )
    assert normalize_url("https://a.com/p?id=1") != normalize_url("https://a.com/p?id=2")


def test_classify_detects_price_broken_across_lines_in_html():
    # Caso real (jujuturismo.tripcart.io): o preço aparece junto na tela, mas no código-fonte o
    # "R$" e o valor ficam em linhas e tabulações diferentes dentro do mesmo elemento, sem nenhum
    # botão "Saiba mais" dentro de um <a> (o botão real da página também não é um link). Sem o
    # "\\s*" na PRICE_RE (em vez de "\\s?"), esses cards não eram contados.
    def card_with_broken_price(slug: str, title: str, value: str) -> str:
        return f"""
        <a href="/{slug}">
          <div class="block-trips">
            <img src="/img/{slug}.jpg" width="600" />
            <h4>{title}</h4>
            <h5>
                R$

                {value}
            </h5>
            <div class="see-more"><p>Ver mais</p></div>
          </div>
        </a>
        """

    html = "<html><body>" + "".join(
        card_with_broken_price(f"trip/v{n}", f"Viagem {n}", f"{n}9,99") for n in range(1, 6)
    ) + "</body></html>"
    result = classify_page(html, "https://agencia.com.br/")
    assert result.kind == "central"
    assert len(result.trip_links) == 5
    # O preço capturado não deve carregar as quebras de linha/tabulação do HTML.
    assert result.trip_links[0].price == "R$ 19,99"


# --- Categoria de cada viagem (título da seção antes do grupo de cards) ---


def _tripcart_category(category_id: int, title: str, slugs: list[str]) -> str:
    # Mesma estrutura da home real do jujuturismo.tripcart.io: o título da categoria (<h2> dentro de
    # um link "search?category=...") fica num bloco ANTES do carrossel, não em volta dos cards.
    items = "".join(
        f"""
        <div class="item mb-2"><a href="https://agencia.tripcart.io/trip/{slug}">
          <div class="block-trips"><img src="/img/{slug}.jpg" width="600" /><h4>Viagem {slug}</h4>
            <h5>
                R$

                1{n}9,90
            </h5><div class="see-more"><p>Ver mais</p></div></div></a></div>
        """
        for n, slug in enumerate(slugs)
    )
    return f"""
    <div class="container category-trips">
      <div class="mb-4 text-center flex-container flex-align-center">
        <a href="search?category={category_id}"><h2 class="mb-1">{title} </h2></a>
        <div class="category-divisor global-color"></div>
        <a href="search?category={category_id}"><p data-i18n="seeAll">Ver todas</p></a>
      </div>
      <div class="theme-carousel"><div id="swiper-next"></div><div id="swiper-prev"></div>
        <div class="owl-carousel owl-theme">{items}</div>
      </div>
    </div>
    """


def test_categories_from_heading_before_each_carousel():
    html = (
        "<html><body><div class='swiper-slide'><h1>O mundo é cheio de lugares incríveis</h1></div>"
        "<h2>Como fazer uma reserva?</h2><p>Escolha a viagem, preencha os dados e pague pelo site.</p>"
        + _tripcart_category(1, "Bate e Volta NOVEMBRO DE 2026", ["bonito", "maragogi", "calhetas"])
        + _tripcart_category(2, "Finais de Semana e Pacotes", ["pipa"])
        + _tripcart_category(3, "Passeios Especiais", ["confra", "morango"])
        + "<h2>Entre em contato</h2></body></html>"
    )
    result = classify_page(html, "https://agencia.tripcart.io/")
    assert result.kind == "central"
    by_slug = {link.url.rsplit("/", 1)[-1]: link for link in result.trip_links}
    assert {slug: link.category for slug, link in by_slug.items()} == {
        "bonito": "Bate e Volta NOVEMBRO DE 2026",
        "maragogi": "Bate e Volta NOVEMBRO DE 2026",
        "calhetas": "Bate e Volta NOVEMBRO DE 2026",
        # Categoria com um card só também vale; o nome fica como no site (só sem o espaço do fim).
        "pipa": "Finais de Semana e Pacotes",
        "confra": "Passeios Especiais",
        "morango": "Passeios Especiais",
    }
    assert [by_slug[slug].position for slug in ("bonito", "maragogi", "calhetas", "pipa", "confra", "morango")] == list(range(6))


def test_categories_from_section_headings_in_simple_markup():
    # Outra estrutura comum: <section> com <h2> e uma grade de cards logo abaixo.
    def section(title: str, slugs: list[str]) -> str:
        cards = "".join(_card(f"viagens/{slug}", slug.title()) for slug in slugs)
        return f"<section><h2>{title}</h2><p>Saídas confirmadas.</p><div class='grid'>{cards}</div></section>"

    html = f"<html><body><main>{section('Nacionais', ['gramado', 'bonito'])}{section('Internacionais', ['paris', 'roma', 'lisboa'])}</main></body></html>"
    result = classify_page(html, "https://agencia.com.br/")
    assert [(link.title, link.category) for link in result.trip_links] == [
        ("Gramado", "Nacionais"),
        ("Bonito", "Nacionais"),
        ("Paris", "Internacionais"),
        ("Roma", "Internacionais"),
        ("Lisboa", "Internacionais"),
    ]


def test_group_without_heading_does_not_inherit_previous_category():
    # O segundo carrossel não tem título: não pode herdar "Nacionais" do grupo de cima.
    first = "".join(_card(f"viagens/n{n}", f"Nacional {n}") for n in range(1, 4))
    second = "".join(_card(f"viagens/s{n}", f"Sem título {n}") for n in range(1, 4))
    html = f"""
    <html><body><main>
      <section><h2>Nacionais</h2><div class="grid">{first}</div></section>
      <section><div class="grid">{second}</div></section>
    </main></body></html>
    """
    result = classify_page(html, "https://agencia.com.br/")
    categories = {link.title: link.category for link in result.trip_links}
    assert all(categories[f"Nacional {n}"] == "Nacionais" for n in range(1, 4))
    assert all(categories[f"Sem título {n}"] is None for n in range(1, 4))


def test_no_heading_before_cards_means_no_category():
    cards = "".join(_card(f"viagens/v{n}", f"Viagem {n}") for n in range(1, 6))
    result = classify_page(f"<html><body><div class='grid'>{cards}</div></body></html>", "https://a.com/")
    assert result.kind == "central"
    assert all(link.category is None for link in result.trip_links)


def test_heading_followed_by_long_text_is_not_a_category():
    # Título de uma seção de texto ("Sobre nós") seguido de vários parágrafos antes dos cards.
    cards = "".join(_card(f"viagens/v{n}", f"Viagem {n}") for n in range(1, 6))
    about = "<p>" + "Somos uma agência com mais de vinte anos de estrada levando grupos pelo Brasil. " * 5 + "</p>"
    html = f"<html><body><section><h2>Sobre nós</h2>{about}<div class='grid'>{cards}</div></section></body></html>"
    result = classify_page(html, "https://a.com/")
    assert all(link.category is None for link in result.trip_links)


def test_card_titles_outside_card_block_are_not_categories():
    # O título de cada card fica fora do bloco achado (só foto e preço dentro do link). Cada card
    # "teria" a própria categoria, todas com um card só: são títulos de card, não seções.
    cards = "".join(
        f'<div class="t"><h3>Destino {n}</h3><a href="/v/{n}"><img src="/i{n}.jpg"/><span>R$ {n}90,00</span></a></div>'
        for n in range(1, 6)
    )
    result = classify_page(f"<html><body><div class='grid'>{cards}</div></body></html>", "https://a.com/")
    assert result.kind == "central"
    assert all(link.category is None for link in result.trip_links)


def test_heading_inside_menu_or_footer_is_ignored():
    cards = "".join(_card(f"viagens/v{n}", f"Viagem {n}") for n in range(1, 6))
    html = f"<html><body><nav><h2>Menu</h2></nav><div class='grid'>{cards}</div></body></html>"
    result = classify_page(html, "https://a.com/")
    assert all(link.category is None for link in result.trip_links)
