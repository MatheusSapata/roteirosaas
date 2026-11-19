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
