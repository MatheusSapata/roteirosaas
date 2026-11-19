from app.services.custom_domain_links import strip_agency_slug_from_links


def test_remove_slug_da_agencia_dos_links():
    config = {"items": [
        {"url": "/wsviagens/morro-de-sp"},
        {"url": "https://roteiroonline.com/wsviagens/x"},
        {"url": "/wsviagens"},
        {"url": "/wsviagensx/a"},
        {"url": "https://wa.me/55"},
    ]}
    urls = [i["url"] for i in strip_agency_slug_from_links(config, "wsviagens")["items"]]
    assert urls == ["/morro-de-sp", "/x", "/", "/wsviagensx/a", "https://wa.me/55"]


def test_remove_slug_antigo_quando_o_segundo_trecho_e_pagina_da_agencia():
    config = [{"url": "/wsviagens/morro-de-sp"}, {"url": "/outro/foo"}, {"url": "/maragogi"}]
    out = strip_agency_slug_from_links(config, "wsturismoviagens.com", {"morro-de-sp", "maragogi"})
    assert [i["url"] for i in out] == ["/morro-de-sp", "/outro/foo", "/maragogi"]
