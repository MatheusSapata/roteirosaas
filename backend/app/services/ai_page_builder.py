from __future__ import annotations

import re
import secrets
from typing import Any, Dict, Iterable, List

from app.models.agency import Agency
from app.schemas.ai import AiFollowUpAnswers, AiImageSelection, AiManualMedia

PLACEHOLDER_IMAGE = "/placeholder.png"
MediaBundleMap = Dict[str, List[List[str]]]
_HEX_PATTERN = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
DEFAULT_DARK_TEXT = "#0f172a"
DEFAULT_LIGHT_TEXT = "#ffffff"
THEME_SYNC_SECTIONS = {
    "hero",
    "story",
    "banner_card",
    "prices",
    "reasons",
    "itinerary",
    "featured_video",
    "testimonials",
    "faq",
}
_VALID_ASSET_PREFIXES = (
    "http://",
    "https://",
    "data:",
    "/uploads",
    "uploads/",
    "/assets",
    "assets/",
)


def _debug(label: str, value: Any) -> None:
    try:
        print(f"[ai_page_builder] {label}: {value}")
    except Exception:
        print(f"[ai_page_builder] {label}: <unprintable>")


def _normalize_hex_color(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    trimmed = value.strip()
    if not trimmed:
        return None
    match = _HEX_PATTERN.match(trimmed)
    if not match:
        return None
    hex_value = match.group(1)
    if len(hex_value) == 3:
        expanded = "".join(char * 2 for char in hex_value)
    else:
        expanded = hex_value
    return f"#{expanded.lower()}"


def _relative_luminance(color: str | None) -> float:
    normalized = _normalize_hex_color(color)
    if not normalized:
        return 1.0

    r = int(normalized[1:3], 16) / 255
    g = int(normalized[3:5], 16) / 255
    b = int(normalized[5:7], 16) / 255

    linear = []
    for channel in (r, g, b):
        if channel <= 0.03928:
            linear.append(channel / 12.92)
        else:
            linear.append(((channel + 0.055) / 1.055) ** 2.4)

    r_lin, g_lin, b_lin = linear
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def _readable_text_color(background: str | None) -> str:
    normalized = _normalize_hex_color(background)
    if not normalized:
        return DEFAULT_DARK_TEXT
    luminance = _relative_luminance(normalized)
    return DEFAULT_LIGHT_TEXT if luminance < 0.55 else DEFAULT_DARK_TEXT


def _has_media_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False

    trimmed = value.strip()
    if not trimmed:
        return False

    lower = trimmed.lower()
    return lower.startswith(_VALID_ASSET_PREFIXES)


def build_user_prompt(briefing: str, answers: AiFollowUpAnswers) -> str:
    details = []

    if answers.destination:
        details.append(f"Destino principal: {answers.destination}")
    if answers.travel_dates:
        details.append(f"Datas ou período: {answers.travel_dates}")
    if answers.audience:
        details.append(f"Público: {answers.audience}")
    if answers.highlights:
        details.append(f"Diferenciais: {answers.highlights}")
    if answers.pricing:
        details.append(f"Valores e condições: {answers.pricing}")
    if answers.included_services:
        details.append(f"Serviços incluídos: {answers.included_services}")
    if answers.exclusions:
        details.append(f"Não incluso ou observações: {answers.exclusions}")
    if answers.call_to_action:
        details.append(f"Call to action preferido: {answers.call_to_action}")
    if answers.urgency:
        details.append(f"Nível de urgência ou vagas: {answers.urgency}")
    if answers.tone:
        details.append(f"Tom desejado: {answers.tone}")

    details_block = "\n".join(f"- {line}" for line in details if line)
    prompt = [
        "Informações principais enviadas pelo usuário:",
        briefing.strip(),
    ]
    if details_block:
        prompt.append("\nDetalhes complementares confirmados:")
        prompt.append(details_block)
    return "\n".join(prompt).strip()


def sections_to_config(
    sections_plan: List[dict[str, Any]],
    agency: Agency,
    manual_media: List[AiManualMedia],
    generated_media: MediaBundleMap,
    video_url: str | None,
    theme_mode: str | None = None,
) -> dict[str, Any]:
    _debug("sections_to_config.sections_plan", sections_plan)
    _debug("sections_to_config.manual_media", manual_media)
    _debug("sections_to_config.generated_media", generated_media)
    _debug("sections_to_config.video_url", video_url)
    _debug("sections_to_config.theme_mode", theme_mode)

    sections: List[dict[str, Any]] = []

    for plan in sections_plan:
        fields = plan.get("fields") or {}
        section_data: dict[str, Any] = {
            "type": plan.get("type"),
            "enabled": True,
            "anchorId": _build_anchor_id(),
        }
        for key, value in fields.items():
            section_data[key] = value
        sections.append(section_data)

    _debug("sections_to_config.sections_after_plan_copy", sections)
    _reset_dynamic_background_sections(sections)
    _enforce_photo_full_layout(sections)

    _ensure_hero_section(sections, agency)

    if not any(section.get("type") == "agency_footer" for section in sections):
        sections.append(
            {
                "type": "agency_footer",
                "enabled": True,
                "anchorId": _build_anchor_id(),
                "displayVariant": "auto",
                "showCadastur": True,
            }
        )

    _debug("sections_to_config.sections_after_hero_footer", sections)

    media_map = _prepare_media_map(manual_media, generated_media)
    _debug("sections_to_config.media_map", media_map)

    force_placeholders = not manual_media and not any(generated_media.values())
    _debug("sections_to_config.force_placeholders", force_placeholders)

    _apply_media_overrides(sections, media_map, force_placeholders)
    _debug("sections_to_config.sections_after_media_overrides", sections)

    if video_url:
        for section in sections:
            if section.get("type") == "featured_video" and not section.get("videoUrl"):
                section["videoUrl"] = video_url

    _apply_agency_branding_defaults(sections, agency)
    _debug("sections_to_config.sections_after_branding_defaults", sections)

    theme = _build_theme(agency, theme_mode)
    _debug("sections_to_config.theme", theme)

    _apply_theme_overrides(sections, theme_mode, theme)
    _apply_background_alternance(sections, theme)
    _ensure_section_placeholders(sections, force_placeholders)

    _debug("sections_to_config.sections_final", sections)

    return {"sections": sections, "theme": theme}


def _reset_dynamic_background_sections(sections: List[dict[str, Any]]) -> None:
    """
    Some blocks (like countdown) should follow the agency highlight color automatically.
    If the AI model outputs a fixed color, the editor cannot sync it with the highlight picker.
    Clearing those colors lets the front-end apply the proper fallback.
    """
    for section in sections:
        sec_type = (section.get("type") or "").lower()
        if sec_type == "countdown":
            section.pop("backgroundColor", None)
        elif sec_type == "cta":
            section.pop("backgroundColor", None)
            section.pop("highlightColor", None)


def _enforce_photo_full_layout(sections: List[dict[str, Any]]) -> None:
    for section in sections:
        if (section.get("type") or "").lower() == "photo":
            section["layout"] = "full"


def _build_theme(agency: Agency, theme_mode: str | None) -> dict[str, Any]:
    primary = (agency.primary_color or "#1d4ed8").strip()
    secondary = (agency.secondary_color or "#0f172a").strip()

    theme = {
        "color1": "#ffffff",
        "color2": "#f8fafc",
        "heroTheme": "immersive",
        "ctaDefaultColor": primary,
        "ctaTextColor": secondary,
        "sidebarTheme": "light",
    }

    if theme_mode == "dark":
        theme.update(
            {
                "color1": "#050505",
                "color2": "#0C0C0C",
                "ctaTextColor": "#f8fafc",
                "sidebarTheme": "dark",
            }
        )

    return theme


def _apply_theme_overrides(
    sections: List[dict[str, Any]],
    theme_mode: str | None,
    theme: dict[str, Any],
) -> None:
    if theme_mode != "dark":
        return

    base_color = (theme.get("color1") or "#050505").strip()

    for section in sections:
        if section.get("type") != "hero":
            continue
        section["gradientColor"] = base_color
        if not section.get("backgroundColor"):
            section["backgroundColor"] = base_color


def _apply_background_alternance(
    sections: List[dict[str, Any]],
    theme: dict[str, Any],
) -> None:
    color1 = theme.get("color1") or "#ffffff"
    color2 = theme.get("color2") or "#f8fafc"
    alternance = (color1, color2)
    alt_index = 0

    for section in sections:
        sec_type = (section.get("type") or "").lower()

        if sec_type in {"hero", "free_footer_brand"}:
            continue

        if sec_type == "countdown":
            if not _normalize_hex_color(section.get("backgroundColor")):
                section["backgroundColor"] = theme.get("ctaDefaultColor") or color1
            alt_index += 1
            continue

        if sec_type == "cta":
            if not _normalize_hex_color(section.get("backgroundColor")):
                section["backgroundColor"] = theme.get("ctaDefaultColor") or color1
            alt_index += 1
            continue

        if sec_type == "prices":
            selected = alternance[alt_index % 2]
            section["backgroundColor"] = selected
            section["textColor"] = _readable_text_color(selected)
            section.pop("cardColor", None)
            alt_index += 1
            continue

        background = section.get("backgroundColor")
        if not _normalize_hex_color(background):
            selected = alternance[alt_index % 2]
            section["backgroundColor"] = selected
            background = selected

        if sec_type in {"story", "itinerary", "reasons"}:
            section["textColor"] = _readable_text_color(background)

        if sec_type in THEME_SYNC_SECTIONS:
            section.pop("ctaColor", None)

        alt_index += 1


def _prepare_media_map(
    manual_media: List[AiManualMedia],
    generated_media: MediaBundleMap,
) -> MediaBundleMap:
    mapping: MediaBundleMap = {}

    for media in manual_media:
        key = _normalize_media_key((media.section_hint or "generic").lower())
        mapping.setdefault(key, []).append([str(media.url)])

    for key, bundles in generated_media.items():
        normalized_key = _normalize_media_key(key)
        for bundle in bundles or []:
            if not bundle:
                continue
            mapping.setdefault(normalized_key, []).append(list(bundle))

    _debug("_prepare_media_map.mapping", mapping)
    return mapping


def _apply_media_overrides(
    sections: List[dict[str, Any]],
    media_map: MediaBundleMap,
    force_placeholders: bool = False,
) -> None:
    for section in sections:
        sec_type = section.get("type")
        targets = _media_targets_for(sec_type)

        _debug(
            "_apply_media_overrides.inspect",
            {
                "type": sec_type,
                "targets": targets,
                "force_placeholders": force_placeholders,
                "section_before": section,
            },
        )

        if not targets:
            continue

        if force_placeholders:
            if _has_valid_media(section, targets):
                _debug("_apply_media_overrides.skip_force", f"{sec_type} already has media, skipping placeholder")
                continue
            _debug("_apply_media_overrides.action", f"forced placeholder for {sec_type}")
            _apply_placeholder(section, targets, force=True)
            continue

        urls = _resolve_media_for_section(sec_type, media_map)
        _debug(
            "_apply_media_overrides.resolved_urls",
            {"type": sec_type, "urls": urls},
        )

        if not urls:
            _debug("_apply_media_overrides.action", f"placeholder because no urls for {sec_type}")
            _apply_placeholder(section, targets, force=True)
            continue

        _assign_urls(section, targets, urls)


def _has_valid_media(section: dict[str, Any], targets: List[str]) -> bool:
    """
    Check if the section already contains usable media for the specified targets.
    """

    for target in targets:
        if target == "backgroundImage":
            if not _has_media_url(section.get("backgroundImage")):
                return False

        elif target == "image":
            if not _has_media_url(section.get("image")):
                return False

        elif target == "images":
            images = section.get("images")
            valid_images = isinstance(images, list) and any(_has_media_url(img) for img in images)
            if not valid_images:
                return False

        elif target == "days":
            days = section.get("days")
            if not isinstance(days, list) or not days:
                return False
            for day in days:
                if not isinstance(day, dict) or not _has_media_url(day.get("image")):
                    return False

    return True


def _media_targets_for(section_type: str | None) -> List[str]:
    normalized = (section_type or "").lower()
    mapping = {
        "hero": ["backgroundImage", "images"],
        "story": ["images"],
        "gallery": ["images"],
        "photo": ["image"],
        "banner_card": ["backgroundImage"],
        "itinerary": ["days"],
        "reasons": [],
        "prices": [],
        "testimonials": [],
        "cta": [],
    }
    return mapping.get(normalized, [])


def _resolve_media_for_section(section_type: str, media_map: MediaBundleMap) -> List[str]:
    keys = [section_type, "generic"]

    for key in keys:
        bundles = media_map.get(key)
        if bundles:
            bundle = bundles.pop(0)
            _debug(
                "_resolve_media_for_section.hit",
                {
                    "requested_section": section_type,
                    "resolved_key": key,
                    "bundle": bundle,
                    "remaining_for_key": bundles,
                },
            )
            return bundle

    _debug("_resolve_media_for_section.miss", {"requested_section": section_type})
    return []


def _ensure_hero_section(sections: List[dict[str, Any]], agency: Agency) -> None:
    if any(section.get("type") == "hero" for section in sections):
        return

    title = (agency.name or "Roteiro completo").strip() or "Roteiro completo"

    sections.insert(
        0,
        {
            "type": "hero",
            "enabled": True,
            "anchorId": _build_anchor_id(),
            "title": title,
            "subtitle": "Personalize este destaque com destino, data e diferenciais.",
            "chips": [],
            "ctaLabel": "Quero mais detalhes",
            "ctaLink": "",
            "layout": "immersive",
        },
    )


def _ensure_section_placeholders(sections: List[dict[str, Any]], force: bool = False) -> None:
    for section in sections:
        _debug(
            "_ensure_section_placeholders.inspect",
            {
                "type": section.get("type"),
                "force": force,
                "section": section,
            },
        )

        targets = _media_targets_for(section.get("type"))
        if not targets:
            continue

        if force:
            _debug("_ensure_section_placeholders.action", f"forced placeholder for {section.get('type')}")
            _apply_placeholder(section, targets, force=True)
            continue

        if "days" in targets:
            if not force:
                # Allow manual edits (e.g., removing an image from a specific day) without reapplying placeholders.
                continue

            days = section.get("days")

            if isinstance(days, list):
                for day in days:
                    if isinstance(day, dict):
                        valid_day_image = _has_media_url(day.get("image"))
                        _debug(
                            "_ensure_section_placeholders.day_check",
                            {
                                "section_type": section.get("type"),
                                "day": day,
                                "valid_day_image": valid_day_image,
                            },
                        )
                        if not valid_day_image:
                            day["image"] = PLACEHOLDER_IMAGE
            else:
                _debug(
                    "_ensure_section_placeholders.action",
                    f"days missing/invalid for {section.get('type')} -> placeholder",
                )
                _apply_placeholder(section, targets, force=True)

            continue

        needs_placeholder = False

        if "backgroundImage" in targets:
            bg = section.get("backgroundImage")
            valid_bg = _has_media_url(bg)
            _debug(
                "_ensure_section_placeholders.background_check",
                {
                    "section_type": section.get("type"),
                    "backgroundImage": bg,
                    "valid_background": valid_bg,
                },
            )
            if not valid_bg:
                needs_placeholder = True

        if "image" in targets:
            image = section.get("image")
            valid_image = _has_media_url(image)
            _debug(
                "_ensure_section_placeholders.image_check",
                {
                    "section_type": section.get("type"),
                    "image": image,
                    "valid_image": valid_image,
                },
            )
            if not valid_image:
                needs_placeholder = True

        if "images" in targets:
            images = section.get("images")
            valid_images = isinstance(images, list) and any(_has_media_url(img) for img in images)
            _debug(
                "_ensure_section_placeholders.images_check",
                {
                    "section_type": section.get("type"),
                    "images": images,
                    "valid_images": valid_images,
                },
            )
            if not valid_images:
                needs_placeholder = True

        if needs_placeholder:
            _debug(
                "_ensure_section_placeholders.action",
                f"needs placeholder for {section.get('type')}",
            )
            _apply_placeholder(section, targets)


def _assign_urls(section: dict[str, Any], targets: List[str], urls: List[str]) -> None:
    _debug(
        "_assign_urls.before",
        {
            "section_type": section.get("type"),
            "targets": targets,
            "urls": urls,
            "section": section,
        },
    )

    if "backgroundImage" in targets and urls:
        section["backgroundImage"] = urls[0]

    if "image" in targets and urls:
        section["image"] = urls[0]

    if "images" in targets:
        existing = section.get("images") or []
        if not isinstance(existing, list):
            existing = []
        section["images"] = urls + existing

    if "days" in targets:
        days = section.get("days")
        if isinstance(days, list) and days:
            for idx, image in enumerate(urls):
                if idx >= len(days):
                    break
                day = days[idx]
                if isinstance(day, dict):
                    day["image"] = image

    _debug(
        "_assign_urls.after",
        {
            "section_type": section.get("type"),
            "section": section,
        },
    )


def _apply_placeholder(section: dict[str, Any], targets: List[str], force: bool = False) -> None:
    _debug(
        "_apply_placeholder.before",
        {
            "section_type": section.get("type"),
            "targets": targets,
            "force": force,
            "section": section,
        },
    )

    def needs_assignment(value: Any) -> bool:
        return force or not _has_media_url(value)

    if "backgroundImage" in targets and needs_assignment(section.get("backgroundImage")):
        section["backgroundImage"] = PLACEHOLDER_IMAGE

    if "image" in targets and needs_assignment(section.get("image")):
        section["image"] = PLACEHOLDER_IMAGE

    if "images" in targets:
        if force:
            section["images"] = [PLACEHOLDER_IMAGE]
        else:
            existing = section.get("images")
            valid = isinstance(existing, list) and any(_has_media_url(item) for item in existing)

            if valid:
                section["images"] = [
                    item if _has_media_url(item) else PLACEHOLDER_IMAGE
                    for item in existing
                ]
            else:
                section["images"] = [PLACEHOLDER_IMAGE]

    if "days" in targets:
        days = section.get("days")

        if isinstance(days, list) and days:
            for day in days:
                if isinstance(day, dict):
                    if force or not _has_media_url(day.get("image")):
                        day["image"] = PLACEHOLDER_IMAGE
            _debug(
                "_apply_placeholder.after",
                {
                    "section_type": section.get("type"),
                    "section": section,
                },
            )
            return

        section["days"] = [
            {
                "day": "Dia 1",
                "title": "Adicione um título",
                "description": "Descreva as atividades deste dia.",
                "image": PLACEHOLDER_IMAGE,
            }
        ]

    _debug(
        "_apply_placeholder.after",
        {
            "section_type": section.get("type"),
            "section": section,
        },
    )


def _build_anchor_id() -> str:
    return f"section-{secrets.token_hex(3)}"


_LACUNA_PATTERN = re.compile(r"\[LACUNA\s*:", re.IGNORECASE)


def _is_missing(value: Any) -> bool:
    if not value:
        return True
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return True
        if _LACUNA_PATTERN.match(cleaned):
            return True
    return False


def _apply_agency_branding_defaults(sections: List[dict[str, Any]], agency: Agency) -> None:
    logo = (agency.logo_url or "").strip()
    primary = (agency.primary_color or "").strip()

    for section in sections:
        sec_type = section.get("type")

        if sec_type == "hero" and logo:
            section["logoUrl"] = logo

        if sec_type == "countdown" and primary and _is_missing(section.get("backgroundColor")):
            section["backgroundColor"] = primary

        if sec_type == "cta" and primary and _is_missing(section.get("backgroundColor")):
            section["backgroundColor"] = primary


def build_image_prompts(
    selections: Iterable[AiImageSelection],
    answers: AiFollowUpAnswers,
) -> List[tuple[AiImageSelection, str]]:
    prompts: List[tuple[AiImageSelection, str]] = []
    focus = (answers.destination or answers.highlights or "viagem inesquecível").strip()

    for selection in selections:
        base = (selection.prompt_hint or "").strip()
        combined = " ".join(part for part in [base, focus] if part).strip() or focus
        prompts.append((selection, combined))

    return prompts


def _normalize_media_key(key: str) -> str:
    if key == "banner":
        return "banner_card"
    return key
