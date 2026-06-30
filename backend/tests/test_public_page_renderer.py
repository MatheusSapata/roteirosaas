from app.schemas.page import PublicPageOut
from app.services.public_page_renderer import _build_meta_block


def _build_page(*, short_description: str | None, seo_description: str | None = None) -> PublicPageOut:
    config = {"general": {"shortDescription": short_description}} if short_description is not None else {}
    return PublicPageOut(
        id=1,
        title="Roteiro Teste",
        slug="roteiro-teste",
        agency_slug="agencia-teste",
        cover_image_url=None,
        seo_title=None,
        seo_description=seo_description,
        config=config,
        branding={"agency_name": "Agência Teste"},
    )


def test_build_meta_block_uses_page_short_description_for_sharing():
    page = _build_page(short_description="Desc. da página")

    meta_block = _build_meta_block(page, "https://example.com/roteiro-teste", "https://example.com")

    assert '<meta property="og:description" content="Desc. da página" />' in meta_block
    assert '<meta name="twitter:description" content="Desc. da página" />' in meta_block


def test_build_meta_block_falls_back_when_short_description_is_empty():
    page = _build_page(short_description="   ")

    meta_block = _build_meta_block(page, "https://example.com/roteiro-teste", "https://example.com")

    assert (
        '<meta property="og:description" content="Agência Teste preparou um roteiro personalizado: Roteiro Teste." />'
        in meta_block
    )
