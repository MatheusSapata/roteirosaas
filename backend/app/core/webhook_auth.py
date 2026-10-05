import logging
import secrets

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def require_webhook_token(
    provided: str | None,
    expected: str | None,
    *,
    env: str,
    setting_name: str,
) -> None:
    """Recusa o webhook quando o token enviado não bate com o configurado.

    Em produção o token é obrigatório: sem ele configurado, nada é processado.
    Em dev/test, sem token configurado, o webhook segue aberto para facilitar testes.
    """
    if not expected:
        if env == "prod":
            logger.error("%s não configurado; webhook recusado.", setting_name)
            raise HTTPException(status_code=503, detail="Webhook não configurado.")
        return
    if not provided or not secrets.compare_digest(provided.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Token do webhook inválido.")
