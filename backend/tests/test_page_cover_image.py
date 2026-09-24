from app.api.v1.endpoints.pages import derive_cover_image_from_config
from app.services.ai_assistant import AI_IMAGE_PLACEHOLDER


def test_ai_placeholder_is_not_saved_in_cover_url_column():
    config = {"sections": [{"type": "hero", "backgroundImage": AI_IMAGE_PLACEHOLDER}]}
    assert len(AI_IMAGE_PLACEHOLDER) > 500
    assert derive_cover_image_from_config(config) is None
    assert config["sections"][0]["backgroundImage"] == AI_IMAGE_PLACEHOLDER


def test_cover_skips_inline_images_and_uses_real_banner_url():
    config = {"sections": [
        {"type": "hero", "backgroundImage": "data:image/svg+xml,test"},
        {"type": "hero", "backgroundImage": "blob:local-image"},
        {"type": "hero", "backgroundImage": "https://example.com/" + "x" * 500},
        {"type": "hero", "enabled": False, "backgroundImage": "/uploads/disabled.jpg"},
        {"type": "hero", "backgroundImage": " /uploads/banner.jpg "},
    ]}
    assert derive_cover_image_from_config(config) == "/uploads/banner.jpg"


def test_cover_accepts_url_at_column_limit():
    url = "https://example.com/" + "x" * (500 - len("https://example.com/"))
    assert derive_cover_image_from_config({"sections": [{"type": "hero", "backgroundImage": url}]}) == url
