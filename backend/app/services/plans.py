from typing import Tuple

from app.models.user import User


def plan_limits(plan: str) -> Tuple[int | None, int | None]:
    """
    Retorna (max_published, max_sections) para o plano.
    max_published: None = ilimitado.
    max_sections: None = sem limite; rodapé free não conta para o limite.
    """
    if plan == "essencial":
        return 5, None
    if plan == "growth":
        return 10, None
    if plan == "infinity":
        return 15, None
    # free
    return 1, 4


def effective_plan(user: User) -> str:
    """
    Determina o plano válido considerando trial ativo, assinatura e plano base.
    """
    if user.trial_plan:
        return user.trial_plan
    if user.subscription and user.subscription.plan:
        return user.subscription.plan
    return user.plan or "free"
