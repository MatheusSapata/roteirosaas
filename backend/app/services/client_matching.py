from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.client import Client


def find_auto_match_client_id(
    *,
    db: Session,
    agency_id: int,
    cpf_normalized: str | None = None,
    email_normalized: str | None = None,
    phone_normalized: str | None = None,
) -> int | None:
    priorities = (
        ("cpf", cpf_normalized, Client.cpf_normalized),
        ("email", email_normalized, Client.email_normalized),
        ("phone", phone_normalized, Client.phone_normalized),
    )

    for _label, value, column in priorities:
        if not value:
            continue
        matches = (
            db.query(Client.id)
            .filter(
                Client.agency_id == agency_id,
                column == value,
                Client.deleted_at.is_(None),
            )
            .limit(2)
            .all()
        )
        if len(matches) == 1:
            return int(matches[0][0])
        if len(matches) > 1:
            return None
    return None


def find_auto_match_client(
    *,
    db: Session,
    agency_id: int,
    cpf_normalized: str | None = None,
    email_normalized: str | None = None,
    phone_normalized: str | None = None,
) -> tuple[int | None, str | None]:
    priorities = (
        ("cpf", cpf_normalized, Client.cpf_normalized),
        ("email", email_normalized, Client.email_normalized),
        ("phone", phone_normalized, Client.phone_normalized),
    )

    for label, value, column in priorities:
        if not value:
            continue
        matches = (
            db.query(Client.id)
            .filter(
                Client.agency_id == agency_id,
                column == value,
                Client.deleted_at.is_(None),
            )
            .limit(2)
            .all()
        )
        if len(matches) == 1:
            return int(matches[0][0]), label
        if len(matches) > 1:
            return None, None
    return None, None
