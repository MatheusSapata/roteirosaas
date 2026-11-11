import pytest

from app.services.url_import import (
    UrlImportError,
    _candidate_images,
    _ensure_public_http_url,
    _extract,
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
