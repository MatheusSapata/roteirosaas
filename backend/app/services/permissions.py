from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


ALL_PERMISSION_KEYS = [
    "dashboard",
    "leads",
    "leads_forms",
    "leads_opportunities",
    "leads_clients",
    "leads_settings",
    "leads_manager",
    "leads_full",
    "pages",
    "pages_viewer",
    "pages_editor",
    "settings",
    "integrations",
    "domains",
    "lessons",
    "team_management",
]


@dataclass(frozen=True)
class PermissionDefinition:
    key: str
    label: str
    route_prefixes: tuple[str, ...]
    backend_permission_key: str
    plans_allowed: tuple[str, ...]
    min_plan_label: str


PERMISSION_CATALOG: dict[str, PermissionDefinition] = {
    "dashboard": PermissionDefinition("dashboard", "Dashboard", ("/api/v1/stats",), "dashboard", ("professional", "agency", "scale", "test"), "Professional"),
    "leads": PermissionDefinition("leads", "Leads", ("/api/v1/lead-forms", "/api/v1/clients"), "leads", ("professional", "agency", "scale", "test"), "Professional"),
    "leads_forms": PermissionDefinition("leads_forms", "Leads: Formulários", ("/api/v1/lead-forms",), "leads_forms", ("professional", "agency", "scale", "test"), "Professional"),
    "leads_opportunities": PermissionDefinition("leads_opportunities", "Leads: Oportunidades", ("/api/v1/clients",), "leads_opportunities", ("professional", "agency", "scale", "test"), "Professional"),
    "leads_clients": PermissionDefinition("leads_clients", "Leads: Clientes", ("/api/v1/clients",), "leads_clients", ("professional", "agency", "scale", "test"), "Professional"),
    "leads_settings": PermissionDefinition("leads_settings", "Leads: Configurações", ("/api/v1/lead-forms",), "leads_settings", ("professional", "agency", "scale", "test"), "Professional"),
    "leads_manager": PermissionDefinition("leads_manager", "Leads: Gerencial", ("/api/v1/lead-forms", "/api/v1/clients"), "leads_manager", ("professional", "agency", "scale", "test"), "Professional"),
    "leads_full": PermissionDefinition("leads_full", "Leads: Total", ("/api/v1/lead-forms", "/api/v1/clients"), "leads_full", ("professional", "agency", "scale", "test"), "Professional"),
    "pages": PermissionDefinition("pages", "Páginas", ("/api/v1/pages", "/api/v1/media"), "pages", ("professional", "agency", "scale", "test"), "Professional"),
    "pages_viewer": PermissionDefinition("pages_viewer", "Páginas: Visualizador", ("/api/v1/pages",), "pages_viewer", ("professional", "agency", "scale", "test"), "Professional"),
    "pages_editor": PermissionDefinition("pages_editor", "Páginas: Editor", ("/api/v1/pages", "/api/v1/media"), "pages_editor", ("professional", "agency", "scale", "test"), "Professional"),
    "settings": PermissionDefinition("settings", "Configurações", ("/api/v1/admin",), "settings", ("scale", "test"), "Scale"),
    "integrations": PermissionDefinition("integrations", "Integrações", ("/api/v1/pixels", "/api/v1/agencies/me/domains"), "integrations", ("professional", "agency", "scale", "test"), "Professional"),
    "domains": PermissionDefinition("domains", "Domínios", ("/api/v1/agencies/me/domains",), "domains", ("professional", "agency", "scale", "test"), "Professional"),
    "lessons": PermissionDefinition("lessons", "Aulas", ("/api/v1/lessons",), "lessons", ("professional", "agency", "scale", "test"), "Professional"),
    "team_management": PermissionDefinition("team_management", "Equipe", ("/api/v1/agency/team",), "team_management", ("professional", "agency", "scale", "test"), "Professional"),
}


PLAN_ALIASES = {
    "free": "free",
    "trial": "professional",
    "essencial": "professional",
    "professional": "professional",
    "profissional": "professional",
    "growth": "agency",
    "agency": "agency",
    "agencia": "agency",
    "infinity": "scale",
    "scale": "scale",
    "escala": "scale",
    "teste": "test",
    "test": "test",
}

PLAN_EXTRA_USER_LIMITS: dict[str, int | None] = {
    "professional": 1,
    "agency": 3,
    "scale": 5,
    "test": None,
    "free": 0,
}


def normalize_plan(plan: str | None) -> str:
    key = (plan or "free").strip().lower()
    return PLAN_ALIASES.get(key, key if key in PLAN_EXTRA_USER_LIMITS else "free")


def allowed_permission_keys_for_plan(plan: str | None) -> set[str]:
    normalized = normalize_plan(plan)
    allowed: set[str] = set()
    for key, definition in PERMISSION_CATALOG.items():
        if normalized in definition.plans_allowed:
            allowed.add(key)
    if normalized == "free":
        allowed.update({"dashboard", "pages"})
    return allowed


def sanitize_requested_permissions(requested: Iterable[str], plan: str | None) -> list[str]:
    allowed = allowed_permission_keys_for_plan(plan)
    selected = {key for key in requested if key in ALL_PERMISSION_KEYS and key in allowed}
    if "pages_editor" in selected:
        selected.discard("pages_viewer")
    if "leads_full" in selected:
        selected.discard("leads_manager")
    return sorted(selected)


def final_permissions_for_member(
    *,
    user_is_owner: bool,
    user_role: str | None = None,
    selected_permissions: Iterable[str] | None,
    plan: str | None,
) -> list[str]:
    allowed_by_plan = allowed_permission_keys_for_plan(plan)
    normalized_role = (user_role or "member").lower()
    if user_is_owner or normalized_role in {"admin", "owner"}:
        return sorted(allowed_by_plan)
    if normalized_role == "editor":
        editor_defaults = {
            "dashboard",
            "pages_editor",
            "leads_forms",
            "leads_opportunities",
            "leads_clients",
            "leads_settings",
            "leads_full",
        }
        effective = allowed_by_plan.intersection(editor_defaults)
        effective.add("pages")
        if any(key in effective for key in ("leads_forms", "leads_opportunities", "leads_clients", "leads_settings", "leads_full")):
            effective.add("leads")
        return sorted(effective)
    if normalized_role == "viewer":
        viewer_defaults = {
            "dashboard",
            "pages_viewer",
            "leads",
            "leads_forms",
            "leads_opportunities",
            "leads_clients",
            "leads_settings",
            "integrations",
            "domains",
        }
        effective = allowed_by_plan.intersection(viewer_defaults)
        if "pages_viewer" in effective:
            effective.add("pages")
        if any(key in effective for key in ("leads", "leads_forms", "leads_opportunities", "leads_clients", "leads_settings")):
            effective.add("leads")
        return sorted(effective)
    selected = set(selected_permissions or [])
    effective = allowed_by_plan.intersection(selected)
    if "pages_editor" in effective or "pages_viewer" in effective:
        effective.add("pages")
    if any(
        key in effective
        for key in ("leads_forms", "leads_opportunities", "leads_clients", "leads_settings", "leads_manager", "leads_full")
    ):
        effective.add("leads")
    return sorted(effective)


def plan_extra_user_limit(plan: str | None) -> int | None:
    return PLAN_EXTRA_USER_LIMITS.get(normalize_plan(plan), 0)


def permission_required_for_path(path: str) -> str | None:
    for key, definition in PERMISSION_CATALOG.items():
        for prefix in definition.route_prefixes:
            if prefix and path.startswith(prefix):
                return key
    return None
