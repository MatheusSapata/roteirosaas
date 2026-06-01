from typing import Tuple

from app.models.user import User


def plan_limits(plan: str) -> Tuple[int | None, int | None]:
    """
    Retorna (max_pages, max_sections) para o plano.
    max_pages: None = ilimitado e considera todas as paginas criadas (publicadas ou rascunhos).
    max_sections: None = sem limite; rodape free nao conta para o limite.
    """
    normalized = str(plan or "").strip().lower()
    aliases = {
        "profissional": "essencial",
        "professional": "essencial",
        "agencia": "growth",
        "agency": "growth",
        "escala": "infinity",
        "scale": "infinity",
        "test": "teste",
    }
    normalized = aliases.get(normalized, normalized or "free")

    if normalized == "trial":
        return 3, None
    if normalized == "essencial":
        return 3, None
    if normalized == "growth":
        return 10, None
    if normalized in {"infinity", "teste"}:
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
