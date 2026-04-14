from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import or_

# Ensure the backend package is on sys.path when running as a script
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal  # noqa: E402
from app.models.cakto import CaktoEventLog  # noqa: E402
from app.models.subscription import Subscription  # noqa: E402
from app.services.cakto import CaktoIntegrationService  # noqa: E402


def _build_order_mapping(service: CaktoIntegrationService) -> dict[str, str]:
    """Return a dictionary order_id -> subscription_id from stored webhook payloads."""
    mapping: dict[str, str] = {}
    logs = service.db.query(CaktoEventLog).all()
    for log in logs:
        payload = log.payload or {}
        try:
            order = service._extract_order(payload)
            subscription_code = service._extract_subscription_code(payload, order)
            order_id = service._extract_order_id(payload)
        except Exception:  # pragma: no cover - utilitário best effort
            continue
        if order_id and subscription_code:
            mapping.setdefault(order_id, subscription_code)
    return mapping


def main() -> None:
    """Fix subscriptions that saved the Cakto order id instead of the subscription id."""
    db = SessionLocal()
    try:
        service = CaktoIntegrationService(db)
        order_map = _build_order_mapping(service)
        if not order_map:
            print("Não encontrei nenhum payload com dados suficientes para corrigir.")
            return

        candidates = (
            db.query(Subscription)
            .filter(Subscription.provider == "cakto")
            .filter(Subscription.cakto_order_id.isnot(None))
            .filter(
                or_(
                    Subscription.cakto_subscription_code.is_(None),
                    Subscription.cakto_subscription_code == Subscription.cakto_order_id,
                )
            )
        )

        processed = updated = 0
        missing: list[int] = []
        for subscription in candidates:
            processed += 1
            new_code = order_map.get(subscription.cakto_order_id)
            if not new_code and subscription.external_reference:
                new_code = order_map.get(subscription.external_reference)
            if not new_code:
                missing.append(subscription.id)
                continue
            if subscription.cakto_subscription_code == new_code:
                continue
            subscription.cakto_subscription_code = new_code
            db.add(subscription)
            updated += 1

        db.commit()
        print(f"{processed} assinaturas analisadas; {updated} atualizadas.")
        if missing:
            print("Assinaturas sem correspondência automática:", ", ".join(map(str, missing)))
    finally:
        db.close()


if __name__ == "__main__":
    main()
