from __future__ import annotations

import logging
import smtplib
import ssl
import base64
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import TYPE_CHECKING

from app.core.config import get_settings
from pathlib import Path

if TYPE_CHECKING:  # pragma: no cover
    from app.models.cakto import CaktoOnboardingToken
    from app.models.user import User

logger = logging.getLogger(__name__)


class EmailClient:
    """Envio simples de e-mails transacionais via SMTP."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def _is_configured(self) -> bool:
        cfg = self.settings
        return bool(cfg.smtp_host and cfg.smtp_username and cfg.smtp_password)

    def send_email(self, *, to_email: str, subject: str, html_body: str, text_body: str | None = None) -> None:
        if not self._is_configured():
            logger.info("SMTP nao configurado. Ignorando envio para %s", to_email)
            return

        cfg = self.settings
        from_email = cfg.smtp_from_email or cfg.smtp_username
        from_name = cfg.smtp_from_name or cfg.app_name

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = formataddr((from_name, from_email))
        message["To"] = to_email
        if cfg.smtp_reply_to:
            message["Reply-To"] = cfg.smtp_reply_to

        if text_body:
            message.attach(MIMEText(text_body, "plain", "utf-8"))
        message.attach(MIMEText(html_body, "html", "utf-8"))

        context = ssl.create_default_context()
        server: smtplib.SMTP | smtplib.SMTP_SSL | None = None
        try:
            if cfg.smtp_use_ssl:
                server = smtplib.SMTP_SSL(cfg.smtp_host, cfg.smtp_port, context=context, timeout=30)
            else:
                server = smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=30)
                server.ehlo()
                if cfg.smtp_use_tls:
                    server.starttls(context=context)
                    server.ehlo()
            server.login(cfg.smtp_username, cfg.smtp_password)
            server.sendmail(from_email, [to_email], message.as_string())
        except Exception as exc:  # pragma: no cover - depende do ambiente SMTP
            logger.exception("Falha ao enviar e-mail para %s: %s", to_email, exc)
        finally:
            if server:
                try:
                    server.quit()
                except Exception:  # pragma: no cover - limpeza melhor esforco
                    logger.debug("Nao foi possivel encerrar conexao SMTP com seguranca.")


def _plan_label(plan_key: str | None) -> str:
    if not plan_key:
        return "seu plano"
    mapping = {
        "essencial": "plano Essencial",
        "growth": "plano Growth",
        "infinity": "plano Infinity",
        "teste": "plano Teste",
    }
    return mapping.get(plan_key.lower(), f"plano {plan_key}")


def _cycle_label(cycle: str | None) -> str:
    if not cycle:
        return ""
    normalized = cycle.lower()
    if normalized in {"monthly", "mensal"}:
        return "ciclo mensal"
    if normalized in {"annual", "anual"}:
        return "ciclo anual"
    return f"ciclo {cycle}"


def _resolve_logo_src() -> str | None:
    settings = get_settings()
    if settings.email_logo_url:
        return settings.email_logo_url
    if settings.email_logo_path:
        path = Path(settings.email_logo_path)
        if path.exists():
            mime, _ = mimetypes.guess_type(path.name)
            if not mime:
                mime = "image/png"
            try:
                data = path.read_bytes()
                b64 = base64.b64encode(data).decode("ascii")
                return f"data:{mime};base64,{b64}"
            except Exception:  # pragma: no cover - file read issues
                logger.exception("Nao foi possivel carregar logo em %s", path)
    return None


def send_cakto_onboarding_email(
    *,
    user: "User",
    onboarding_token: "CaktoOnboardingToken",
    plan_key: str,
    cycle: str,
) -> None:
    """Dispara o e-mail de boas-vindas apos um checkout concluido na Cakto."""

    settings = get_settings()
    client = EmailClient()
    if not client._is_configured():
        logger.info("SMTP nao configurado. Onboarding para %s nao sera enviado.", user.email)
        return

    password_url = f"{settings.resolved_webapp_base_url}/create-password?token={onboarding_token.token}"
    plan_label = _plan_label(plan_key)
    cycle_label = _cycle_label(cycle)
    greeting_name = user.name or user.email

    subject = "Bem-vindo ao Roteiro Online"
    text_body = (
        f"Ola {greeting_name},\n\n"
        f"Seu {plan_label} ja esta ativo{(' (' + cycle_label + ')') if cycle_label else ''}.\n"
        "Para acessar o painel, finalize seu cadastro criando uma senha segura neste link:\n"
        f"{password_url}\n\n"
        "Se precisar de ajuda basta responder este e-mail.\n"
        "Equipe Roteiro Online"
    )
    html_body = f"""
        <p>Ola {greeting_name},</p>
        <p>Seu {plan_label} {cycle_label or ''} ja esta liberado. Para acessar o painel, finalize seu cadastro criando uma senha:</p>
        <p style="margin: 24px 0;">
            <a href="{password_url}" style="background-color:#41ce5f;color:#fff;padding:12px 20px;border-radius:999px;font-weight:bold;text-decoration:none;">
                Definir minha senha
            </a>
        </p>
        <p>Se o botao nao funcionar, copie e cole o link abaixo no navegador:</p>
        <p style="word-break:break-all;"><a href="{password_url}">{password_url}</a></p>
        <p>Qualquer duvida, basta responder este e-mail.</p>
        <p>Equipe Roteiro Online</p>
    """

    logo_src = _resolve_logo_src()
    if logo_src:
        html_body += f"""
        <p style="margin-top:32px;">
            <img src="{logo_src}" alt="Roteiro Online" style="height:48px;">
        </p>
    """

    client.send_email(to_email=user.email, subject=subject, html_body=html_body, text_body=text_body)
