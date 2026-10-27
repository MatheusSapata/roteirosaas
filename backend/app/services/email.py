from __future__ import annotations

import logging
import threading
from html import escape
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import TYPE_CHECKING

from app.core.config import get_settings

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
    if normalized in {"quarterly", "trimestral"}:
        return "ciclo trimestral"
    if normalized in {"annual", "anual"}:
        return "ciclo anual"
    return f"ciclo {cycle}"


def send_in_background(func, /, **kwargs) -> None:
    """Envia sem segurar a resposta (webhook, formulário): o SMTP pode levar segundos e falha só no log."""

    def run() -> None:
        try:
            func(**kwargs)
        except Exception:  # pragma: no cover - envio de e-mail nunca quebra o fluxo de quem chamou
            logger.exception("Falha ao enviar e-mail em segundo plano (%s)", getattr(func, "__name__", "?"))

    threading.Thread(target=run, daemon=True).start()


# ---------------------------------------------------------------------------
# Visual dos e-mails: tabelas e estilos inline (é o que os leitores de e-mail aceitam).
# ---------------------------------------------------------------------------
_BRAND_GREEN = "#41ce5f"
_FONT = "Arial,Helvetica,sans-serif"


def _logo_url() -> str:
    return f"{get_settings().resolved_webapp_base_url}/email/logo-roteiro-online.png"


def _paragraph(html: str) -> str:
    return f'<p style="margin:0 0 14px;font-size:16px;line-height:1.55;color:#33423a;">{html}</p>'


def _email_layout(
    *,
    eyebrow: str,
    title: str,
    body_html: str,
    button_url: str,
    button_label: str,
    note_html: str,
    highlight: str | None = None,
    show_link: bool = True,
) -> str:
    """Moldura única dos e-mails: faixa verde com a logo, cartão branco, botão e aviso no rodapé."""

    settings = get_settings()
    support = settings.smtp_reply_to or settings.smtp_from_email or "suporte@roteiroonline.com"
    highlight_html = (
        f'<div style="background:#f1f8f3;border-radius:12px;padding:14px 16px;margin:6px 0 18px;'
        f'font-size:15px;color:#1f3a2a;">{highlight}</div>'
        if highlight
        else ""
    )
    link_html = (
        '<p style="margin:18px 0 0;font-size:13px;line-height:1.5;color:#6b7a72;">'
        "Se o botão não funcionar, copie e cole este link no navegador:<br>"
        f'<a href="{button_url}" style="color:#0e7a55;word-break:break-all;">{button_url}</a></p>'
        if show_link
        else ""
    )
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#eef2ee;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#eef2ee;"><tr><td align="center" style="padding:28px 12px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:18px;overflow:hidden;font-family:{_FONT};color:#17201b;">
    <tr><td align="center" style="background:{_BRAND_GREEN};padding:26px 32px;">
      <img src="{_logo_url()}" alt="Roteiro Online" width="170" style="display:block;width:170px;max-width:100%;height:auto;border:0;">
    </td></tr>
    <tr><td style="padding:34px 32px 8px;">
      <p style="margin:0 0 10px;font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:#6b7a72;font-weight:700;">{eyebrow}</p>
      <h1 style="margin:0 0 14px;font-size:25px;line-height:1.25;color:#0f1f14;">{title}</h1>
      {body_html}
      {highlight_html}
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:10px 0 4px;">
        <a href="{button_url}" style="display:inline-block;background:{_BRAND_GREEN};color:#0f1f14;text-decoration:none;font-weight:700;font-size:16px;padding:15px 34px;border-radius:999px;">{button_label}</a>
      </td></tr></table>
      {link_html}
    </td></tr>
    <tr><td style="background:#fafbfa;border-top:1px solid #e6ece8;padding:18px 32px;font-size:13px;line-height:1.5;color:#6b7a72;">{note_html}</td></tr>
  </table>
  <p style="max-width:560px;margin:16px auto 0;font-family:{_FONT};font-size:12px;line-height:1.6;color:#7a8780;text-align:center;">
    Roteiro Online · Suporte: {escape(support)}<br>Você recebeu este e-mail porque há uma conta com este endereço no Roteiro Online.
  </p>
</td></tr></table>
</body></html>"""


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

    password_url = f"{settings.resolved_webapp_base_url}/create-password"
    plan_label = _plan_label(plan_key)
    cycle_label = _cycle_label(cycle)
    greeting_name = user.name or user.email
    plan_text = f"{plan_label} ({cycle_label})" if cycle_label else plan_label

    subject = "Bem-vindo ao Roteiro Online"
    text_body = (
        f"Olá, {greeting_name}.\n\n"
        f"Seu {plan_text} já está ativo.\n"
        "Para acessar o painel, finalize seu cadastro criando uma senha segura neste link:\n"
        f"{password_url}\n\n"
        "Se precisar de ajuda, basta responder este e-mail.\n"
        "Equipe Roteiro Online"
    )
    html_body = _email_layout(
        eyebrow="Compra confirmada",
        title=f"Bem-vindo ao Roteiro Online, {escape(greeting_name)}!",
        body_html=_paragraph("A sua assinatura já está ativa. Falta só um passo: criar a sua senha para entrar no painel."),
        highlight=f"<b>{escape(plan_label.capitalize())}</b>" + (f" · {escape(cycle_label)}" if cycle_label else ""),
        button_url=password_url,
        button_label="Criar minha senha",
        note_html="Precisa de ajuda? É só responder este e-mail que a nossa equipe te atende.",
    )
    client.send_email(to_email=user.email, subject=subject, html_body=html_body, text_body=text_body)


def send_team_invite_email(
    *,
    to_email: str,
    invitee_name: str,
    inviter_name: str,
    agency_name: str,
    invite_url: str,
    expires_days: int = 7,
) -> None:
    settings = get_settings()
    client = EmailClient()
    if not client._is_configured():
        logger.info("SMTP nao configurado. Convite de equipe para %s nao sera enviado.", to_email)
        return

    subject = f"Convite para acessar a equipe da {agency_name}"
    safe_invitee = invitee_name or to_email
    safe_inviter = inviter_name or "Administrador"
    app_name = settings.app_name or "Roteiro Online"
    text_body = (
        f"Olá, {safe_invitee}.\n\n"
        f"Você foi convidado por {safe_inviter} para fazer parte da equipe da {agency_name} no {app_name}.\n\n"
        "Clique no link abaixo para criar sua senha e acessar sua conta:\n"
        f"{invite_url}\n\n"
        f"Este convite expira em {expires_days} dias.\n"
        "Se você não esperava este convite, ignore este e-mail."
    )
    html_body = _email_layout(
        eyebrow="Convite de equipe",
        title=f"Olá, {escape(safe_invitee)}. Você foi convidado!",
        body_html=_paragraph(
            f"<b>{escape(safe_inviter)}</b> convidou você para fazer parte da equipe da "
            f"<b>{escape(agency_name)}</b> no {escape(app_name)}. Aceite o convite para criar a sua senha e acessar a conta."
        ),
        button_url=invite_url,
        button_label="Aceitar convite",
        note_html=f"<b>O convite vale por {expires_days} dias.</b> Se você não esperava este convite, pode ignorar este e-mail.",
    )
    client.send_email(to_email=to_email, subject=subject, html_body=html_body, text_body=text_body)


def send_checkout_welcome_email(
    *,
    to_email: str,
    name: str | None,
    plan_key: str | None,
    cycle: str | None,
    password_url: str,
) -> None:
    """Cliente novo que acabou de pagar pelo checkout (Asaas): confirma a compra e leva a definir a senha."""

    client = EmailClient()
    if not client._is_configured():
        logger.info("SMTP nao configurado. Boas-vindas para %s nao serao enviadas.", to_email)
        return
    plan_label = _plan_label(plan_key)
    cycle_label = _cycle_label(cycle)
    greeting = name or to_email
    plan_text = f"{plan_label} ({cycle_label})" if cycle_label else plan_label
    subject = "Pagamento confirmado: bem-vindo ao Roteiro Online"
    text_body = (
        f"Olá, {greeting}.\n\n"
        f"Recebemos o seu pagamento e o {plan_text} já está ativo.\n"
        "Para acessar o painel, crie a sua senha neste link:\n"
        f"{password_url}\n\n"
        "Se precisar de ajuda, basta responder este e-mail.\n"
        "Equipe Roteiro Online"
    )
    html_body = _email_layout(
        eyebrow="Pagamento confirmado",
        title=f"Bem-vindo ao Roteiro Online, {escape(greeting)}!",
        body_html=_paragraph(
            "Recebemos o seu pagamento e a sua assinatura já está ativa. "
            "Falta só um passo: criar a sua senha para entrar no painel e montar o seu primeiro roteiro."
        ),
        highlight=f"<b>{escape(plan_label.capitalize())}</b>" + (f" · {escape(cycle_label)}" if cycle_label else ""),
        button_url=password_url,
        button_label="Criar minha senha",
        note_html="Precisa de ajuda? É só responder este e-mail que a nossa equipe te atende.",
    )
    client.send_email(to_email=to_email, subject=subject, html_body=html_body, text_body=text_body)


def send_password_reset_email(*, to_email: str, name: str | None, reset_url: str, expires_minutes: int) -> None:
    client = EmailClient()
    if not client._is_configured():
        logger.info("SMTP nao configurado. Redefinicao de senha para %s nao sera enviada.", to_email)
        return
    greeting = name or to_email
    hours = expires_minutes // 60
    validity = f"{hours} hora{'s' if hours != 1 else ''}" if expires_minutes % 60 == 0 and hours else f"{expires_minutes} minutos"
    subject = "Redefinir a sua senha do Roteiro Online"
    text_body = (
        f"Olá, {greeting}.\n\n"
        "Recebemos um pedido para redefinir a sua senha. Use o link abaixo:\n"
        f"{reset_url}\n\n"
        f"O link vale por {validity}. Se você não pediu, ignore este e-mail: a sua senha continua a mesma.\n"
        "Equipe Roteiro Online"
    )
    html_body = _email_layout(
        eyebrow="Recuperar acesso",
        title=f"Olá, {escape(greeting)}. Vamos criar uma nova senha?",
        body_html=_paragraph("Recebemos um pedido para redefinir a senha da sua conta. Clique no botão abaixo para escolher uma nova."),
        button_url=reset_url,
        button_label="Redefinir minha senha",
        note_html=f"<b>O link vale por {validity}.</b> Se você não pediu a redefinição, pode ignorar este e-mail: a sua senha continua a mesma.",
    )
    client.send_email(to_email=to_email, subject=subject, html_body=html_body, text_body=text_body)
