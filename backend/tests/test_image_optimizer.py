import io

from PIL import Image

from app.schemas.page import PublicPageOut
from app.services.image_optimizer import VARIANT_WIDTHS, optimize_image
from app.services.public_page_renderer import _hero_preload_tags, _page_data_script


def _encode(image: Image.Image, fmt: str, **options) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, fmt, **options)
    return buffer.getvalue()


def test_photo_becomes_webp_in_three_widths_with_camera_orientation():
    exif = Image.Exif()
    exif[0x0112] = 6  # foto de celular "deitada": gira 90°
    raw = _encode(Image.new("RGB", (4000, 3000), (40, 120, 200)), "JPEG", quality=95, exif=exif)

    variants = optimize_image(raw)

    assert variants is not None and set(variants) == set(VARIANT_WIDTHS)
    sizes = {width: Image.open(io.BytesIO(data)).size for width, data in variants.items()}
    assert sizes[2400] == (2400, 3200)
    assert sizes[640] == (640, 853)
    assert all(Image.open(io.BytesIO(data)).format == "WEBP" for data in variants.values())


def test_transparent_logo_keeps_alpha_and_small_image_is_not_enlarged():
    logo = Image.new("RGBA", (300, 100), (0, 0, 0, 0))
    logo.paste((14, 122, 83, 255), (20, 20, 120, 80))

    variants = optimize_image(_encode(logo, "PNG"))

    assert variants is not None
    image = Image.open(io.BytesIO(variants[2400]))
    assert image.mode == "RGBA" and image.size == (300, 100)


def test_gif_and_unknown_files_are_kept_as_sent():
    assert optimize_image(_encode(Image.new("P", (20, 20)), "GIF")) is None
    assert optimize_image(b"not an image") is None


def _page(sections, design_v2_enabled=True, branding=None):
    return PublicPageOut(
        id=1,
        title="Roteiro",
        slug="roteiro",
        agency_slug="agencia",
        config={"sections": sections},
        branding=branding or {},
        design_v2_enabled=design_v2_enabled,
    )


def _images(tags):
    return [tag for tag in tags if 'as="image"' in tag]


def test_hero_photo_is_preloaded_with_the_same_srcset_as_the_page():
    image = "https://cdn.example.com/m/abc_2400.webp"
    mobile = "https://cdn.example.com/m/mob_2400.webp"
    tags = _hero_preload_tags(
        _page([{"type": "header", "enabled": True}, {"type": "hero", "enabled": True, "backgroundImage": image, "mobileBackgroundImage": mobile}])
    )

    images = _images(tags)
    assert len(images) == 2
    assert 'imagesrcset="https://cdn.example.com/m/abc_640.webp 640w, https://cdn.example.com/m/abc_1280.webp 1280w, ' in images[0]
    assert 'media="(min-width: 641px)"' in images[0]
    assert 'href="https://cdn.example.com/m/mob_2400.webp"' in images[1] and 'media="(max-width: 640px)"' in images[1]
    assert any("fonts.googleapis.com" in tag and "media=\"print\"" in tag for tag in tags)


def test_agency_logo_is_preloaded_with_the_page_header():
    logo = "https://cdn.example.com/m/logo_2400.webp"
    tags = _hero_preload_tags(_page([{"type": "header", "enabled": True}, {"type": "prices", "enabled": True}], branding={"logo_url": logo}))
    assert _images(tags) == [
        f'<link rel="preload" as="image" href="{logo}" fetchpriority="high" '
        'imagesrcset="https://cdn.example.com/m/logo_640.webp 640w, https://cdn.example.com/m/logo_1280.webp 1280w, '
        f'{logo} 2400w" imagesizes="320px" />'
    ]


def test_no_image_preload_when_hero_is_not_first_or_page_uses_old_design():
    hero = {"type": "hero", "enabled": True, "backgroundImage": "https://cdn.example.com/m/a.jpg"}
    assert _images(_hero_preload_tags(_page([{"type": "prices", "enabled": True}, hero]))) == []
    assert _hero_preload_tags(_page([hero], design_v2_enabled=False)) == []
    assert _images(_hero_preload_tags(_page([{**hero, "videoUrl": "https://youtu.be/abc"}]))) == []
    assert _images(_hero_preload_tags(_page([{**hero, "backgroundImage": "/uploads/a.jpg"}]))) == []


def test_page_data_goes_in_the_html_safely_for_the_open_address():
    import json

    page = _page([{"type": "hero", "enabled": True, "title": "</script><script>alert(1)</script>"}])
    tag = _page_data_script(page, "/agencia/roteiro")

    assert tag.count("</script>") == 1  # só o fechamento da própria tag
    body = tag[len('<script id="ro-page-data" type="application/json">') : -len("</script>")]
    data = json.loads(body)
    assert data["path"] == "/agencia/roteiro"
    assert data["page"]["config"]["sections"][0]["title"] == "</script><script>alert(1)</script>"
