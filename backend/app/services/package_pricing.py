from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping, Sequence

from fastapi import HTTPException

from app.models.product import ProductVariation

_PRICING_MODES = {"free", "extra"}


@dataclass
class ChildPricingRule:
    key: str
    label: str
    min_age: int
    max_age: int
    enabled: bool
    pricing_mode: str
    extra_amount_cents: int
    counts_towards_capacity: bool
    counts_as_passenger: bool
    max_quantity: int | None

    def serialize(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "min_age": self.min_age,
            "max_age": self.max_age,
            "enabled": self.enabled,
            "pricing_mode": self.pricing_mode,
            "extra_amount_cents": self.extra_amount_cents,
            "counts_towards_capacity": self.counts_towards_capacity,
            "counts_as_passenger": self.counts_as_passenger,
            "max_quantity": self.max_quantity,
        }


@dataclass
class ChildBreakdownItem:
    key: str
    label: str
    quantity: int
    unit_amount_cents: int
    total_amount_cents: int
    counts_towards_capacity: bool
    counts_as_passenger: bool

    def serialize(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "quantity": self.quantity,
            "unit_amount_cents": self.unit_amount_cents,
            "total_amount_cents": self.total_amount_cents,
            "counts_towards_capacity": self.counts_towards_capacity,
            "counts_as_passenger": self.counts_as_passenger,
        }


@dataclass
class PackageComposition:
    base_price_cents: int
    child_extra_cents: int
    total_price_cents: int
    base_passengers: int
    child_passengers: int
    total_passengers: int
    base_capacity: int
    child_capacity: int
    total_capacity: int
    child_breakdown: list[ChildBreakdownItem]
    child_quantities: dict[str, int]


_DEFAULT_RULES: dict[str, ChildPricingRule] = {
    "under_5": ChildPricingRule(
        key="under_5",
        label="Menores de 5 anos",
        min_age=0,
        max_age=4,
        enabled=False,
        pricing_mode="free",
        extra_amount_cents=0,
        counts_towards_capacity=False,
        counts_as_passenger=True,
        max_quantity=None,
    ),
    "age_5_12": ChildPricingRule(
        key="age_5_12",
        label="De 5 a 12 anos",
        min_age=5,
        max_age=12,
        enabled=False,
        pricing_mode="extra",
        extra_amount_cents=0,
        counts_towards_capacity=True,
        counts_as_passenger=True,
        max_quantity=None,
    ),
}


def default_child_pricing_rules() -> list[ChildPricingRule]:
    return [replace(rule) for rule in _DEFAULT_RULES.values()]


def _coerce_int(value: Any, *, minimum: int | None = None) -> int:
    if isinstance(value, bool):
        raise ValueError("boolean is not a valid integer")
    if isinstance(value, (int,)):
        result = int(value)
    elif isinstance(value, float):
        result = int(value)
    elif isinstance(value, str) and value.strip():
        result = int(float(value))
    else:
        result = 0
    if minimum is not None and result < minimum:
        raise ValueError("value below minimum")
    return result


def _parse_pricing_rule(raw: Mapping[str, Any], base: ChildPricingRule) -> ChildPricingRule:
    enabled = bool(raw.get("enabled", base.enabled))
    min_age = _coerce_int(raw.get("min_age", base.min_age), minimum=0)
    max_age = _coerce_int(raw.get("max_age", base.max_age), minimum=min_age)
    pricing_mode = str(raw.get("pricing_mode", base.pricing_mode) or base.pricing_mode).lower()
    if pricing_mode not in _PRICING_MODES:
        pricing_mode = base.pricing_mode
    max_quantity_value = raw.get("max_quantity", base.max_quantity)
    max_quantity = None
    if max_quantity_value is not None:
        max_quantity = _coerce_int(max_quantity_value, minimum=0)
    extra_amount_source = raw.get("extra_amount_cents")
    if extra_amount_source is None and "extra_amount" in raw:
        # allow decimal-based payloads
        extra_amount = float(raw["extra_amount"])
        extra_amount_source = int(round(extra_amount * 100))
    extra_amount_cents = _coerce_int(extra_amount_source if extra_amount_source is not None else base.extra_amount_cents, minimum=0)
    if pricing_mode == "free":
        extra_amount_cents = 0
    counts_capacity = bool(raw.get("counts_towards_capacity", base.counts_towards_capacity))
    counts_passenger = bool(raw.get("counts_as_passenger", base.counts_as_passenger))
    label = str(raw.get("label", base.label) or base.label).strip() or base.label
    return ChildPricingRule(
        key=base.key,
        label=label,
        min_age=min_age,
        max_age=max_age,
        enabled=enabled,
        pricing_mode=pricing_mode,
        extra_amount_cents=extra_amount_cents,
        counts_towards_capacity=counts_capacity,
        counts_as_passenger=counts_passenger,
        max_quantity=max_quantity,
    )


def normalize_child_pricing_rules(raw_rules: Sequence[Mapping[str, Any]] | None) -> list[ChildPricingRule]:
    defaults = {key: replace(rule) for key, rule in _DEFAULT_RULES.items()}
    if raw_rules:
        for raw in raw_rules:
            if not isinstance(raw, Mapping):
                continue
            key = str(raw.get("key") or "").strip()
            if key not in defaults:
                continue
            try:
                defaults[key] = _parse_pricing_rule(raw, defaults[key])
            except (ValueError, TypeError):
                continue
    return [defaults[key] for key in _DEFAULT_RULES.keys()]


def serialize_child_pricing_rules(rules: Sequence[ChildPricingRule]) -> list[dict[str, Any]]:
    return [rule.serialize() for rule in rules]


def _validate_child_counts(children: Mapping[str, Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    for key, raw_value in children.items():
        try:
            quantity = _coerce_int(raw_value, minimum=0)
        except ValueError:
            quantity = 0
        if quantity <= 0:
            continue
        result[str(key)] = quantity
    return result


def calculate_package_composition(
    *,
    variation: ProductVariation,
    quantity: int,
    child_counts: Mapping[str, Any] | None = None,
) -> PackageComposition:
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantidade inválida para o pacote.")
    base_price = (variation.price_cents or 0) * quantity
    people_included = variation.people_included or 0
    base_passengers = max(people_included, 0) * quantity
    raw_slots = getattr(variation, "slots_per_unit", None)
    slots_per_unit = int(raw_slots or 0)
    if slots_per_unit <= 0:
        slots_per_unit = max(people_included, 1)
    base_capacity = max(slots_per_unit * quantity, base_passengers, 1)

    rules = normalize_child_pricing_rules(variation.child_pricing_rules or [])
    counts = _validate_child_counts(child_counts or {})
    if counts and not variation.child_policy_enabled:
        raise HTTPException(status_code=400, detail="Este pacote não aceita crianças.")

    breakdown: list[ChildBreakdownItem] = []
    child_extra_total = 0
    child_passengers = 0
    child_capacity = 0

    for rule in rules:
        quantity_for_rule = counts.get(rule.key, 0)
        if quantity_for_rule <= 0:
            continue
        if not rule.enabled:
            raise HTTPException(status_code=400, detail=f"A faixa infantil {rule.label} está desativada.")
        max_allowed = rule.max_quantity * quantity if rule.max_quantity is not None else None
        if max_allowed is not None and quantity_for_rule > max_allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Quantidade máxima excedida para {rule.label}.",
            )
        unit_amount = 0 if rule.pricing_mode == "free" else rule.extra_amount_cents
        total_amount = unit_amount * quantity_for_rule
        child_extra_total += total_amount
        if rule.counts_as_passenger:
            child_passengers += quantity_for_rule
        if rule.counts_towards_capacity:
            child_capacity += quantity_for_rule
        breakdown.append(
            ChildBreakdownItem(
                key=rule.key,
                label=rule.label,
                quantity=quantity_for_rule,
                unit_amount_cents=unit_amount,
                total_amount_cents=total_amount,
                counts_towards_capacity=rule.counts_towards_capacity,
                counts_as_passenger=rule.counts_as_passenger,
            )
        )

    total_price = base_price + child_extra_total
    total_passengers = base_passengers + child_passengers
    total_capacity = base_capacity + child_capacity

    child_quantities = {
        key: value
        for key, value in ((rule.key, counts.get(rule.key, 0)) for rule in rules)
        if value > 0
    }
    return PackageComposition(
        base_price_cents=base_price,
        child_extra_cents=child_extra_total,
        total_price_cents=total_price,
        base_passengers=base_passengers,
        child_passengers=child_passengers,
        total_passengers=total_passengers,
        base_capacity=base_capacity,
        child_capacity=child_capacity,
        total_capacity=total_capacity,
        child_breakdown=breakdown,
        child_quantities=child_quantities,
    )
