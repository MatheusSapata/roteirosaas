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
