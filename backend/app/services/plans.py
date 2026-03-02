from typing import Tuple

from app.models.user import User


def plan_limits(plan: str) -> Tuple[int | None, int | None]:
    """
    Retorna (max_pages, max_sections) para o plano.
    max_pages: None = ilimitado e considera todas as paginas criadas (publicadas ou rascunhos).
    max_sections: None = sem limite; rodape free nao conta para o limite.
    """
    if plan == "essencial":
        return 3, None
    if plan == "growth":
        return 10, None
    if plan in {"infinity", "teste"}:
        return None, None
    # free
    return 1, 4


def effective_plan(user: User) -> str:
    """
    Determina o plano valido considerando trial ativo, assinatura e plano base.
    """
    if user.trial_plan:
        return user.trial_plan
    if user.subscription and user.subscription.plan:
        return user.subscription.plan
    return user.plan or "free"
