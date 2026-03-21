from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_credit import AiCreditTransaction, AiCreditWallet


class InsufficientCreditsError(Exception):
    pass


def _get_wallet_for_update(db: Session, user_id: int) -> AiCreditWallet:
    wallet = (
        db.execute(
            select(AiCreditWallet).where(AiCreditWallet.user_id == user_id).with_for_update(of=AiCreditWallet)
        )
        .scalars()
        .first()
    )
    if wallet is None:
        wallet = AiCreditWallet(user_id=user_id, balance=0)
        db.add(wallet)
        db.flush()
    return wallet


def grant_credits(db: Session, user_id: int, amount: int, reason: str, metadata: dict[str, Any] | None = None) -> AiCreditWallet:
    if amount <= 0:
        raise ValueError("Amount must be positive to grant credits.")
    wallet = _get_wallet_for_update(db, user_id)
    wallet.balance += amount
    tx = AiCreditTransaction(wallet_id=wallet.id, delta=amount, reason=reason, metadata_json=metadata or {})
    db.add(tx)
    db.flush()
    return wallet


def spend_credits(
    db: Session,
    user_id: int,
    amount: int,
    reason: str,
    metadata: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> AiCreditWallet:
    if amount <= 0:
        raise ValueError("Amount must be positive.")
    wallet = _get_wallet_for_update(db, user_id)
    if wallet.balance < amount:
        raise InsufficientCreditsError("Créditos insuficientes para concluir esta ação.")
    if dry_run:
        return wallet
    wallet.balance -= amount
    tx = AiCreditTransaction(wallet_id=wallet.id, delta=-amount, reason=reason, metadata_json=metadata or {})
    db.add(tx)
    db.flush()
    return wallet


def get_wallet_snapshot(db: Session, user_id: int) -> AiCreditWallet:
    wallet = db.query(AiCreditWallet).filter(AiCreditWallet.user_id == user_id).first()
    if wallet is None:
        wallet = AiCreditWallet(user_id=user_id, balance=0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    return wallet
