from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ViajeChatTag:
    key: str
    label: str
    tag_id: str


# Mapeamento oficial de tags no ViajeChat
VIAJECHAT_TAGS: dict[str, ViajeChatTag] = {
    "checkout_abandoned_agency": ViajeChatTag(
        key="checkout_abandoned_agency",
        label="Abandono de carrinho - Plano Agência",
        tag_id="db606799-5176-4459-81e4-43b6540f01a0",
    ),
    "checkout_abandoned_scale": ViajeChatTag(
        key="checkout_abandoned_scale",
        label="Abandono de carrinho - Plano Escala",
        tag_id="6745068a-4f87-47f2-a947-0d294113cb29",
    ),
    "checkout_abandoned_professional": ViajeChatTag(
        key="checkout_abandoned_professional",
        label="Abandono de carrinho - Plano Profissional",
        tag_id="903d787c-d8e9-49fa-8bb9-16789391f3b8",
    ),
    "signed_agency": ViajeChatTag(
        key="signed_agency",
        label="Assinou Plano Agência",
        tag_id="cce4ba8d-a8a6-4d06-83b4-cfc073a3be17",
    ),
    "signed_scale": ViajeChatTag(
        key="signed_scale",
        label="Assinou Plano Escala",
        tag_id="8343fd43-7624-4968-8c2e-1c8f6a5b138f",
    ),
    "signed_professional": ViajeChatTag(
        key="signed_professional",
        label="Assinou Plano Profissional",
        tag_id="5d505097-2c5a-4db5-a69c-974528f405a8",
    ),
    "plan_active": ViajeChatTag(
        key="plan_active",
        label="Plano Ativo",
        tag_id="7396bceb-9dcd-4944-9c2d-38800c2ec92b",
    ),
    "plan_cancelled": ViajeChatTag(
        key="plan_cancelled",
        label="Plano Cancelado",
        tag_id="a553adb6-9f78-43bd-8712-238cd4d57ec1",
    ),
    "online_itinerary": ViajeChatTag(
        key="online_itinerary",
        label="Roteiro Online",
        tag_id="144a6d15-f56d-4fb4-b6c9-a23392ed1fd4",
    ),
}


def get_viajechat_tag_id(key: str) -> str | None:
    tag = VIAJECHAT_TAGS.get(key)
    return tag.tag_id if tag else None
