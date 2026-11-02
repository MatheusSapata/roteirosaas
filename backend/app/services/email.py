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

    def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
        raise_errors: bool = False,
    ) -> None:
        """Com raise_errors, a falha (inclusive SMTP não configurado) sobe para quem chamou; sem ele,
        fica só no log."""
        if not self._is_configured():
            logger.info("SMTP nao configurado. Ignorando envio para %s", to_email)
            if raise_errors:
                raise RuntimeError("O envio de e-mail (SMTP) não está configurado no servidor.")
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
            if raise_errors:
                raise
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
# Paleta Viaje On de 2026-11 (a mesma do painel em frontend/src/styles/main.css).
_BRAND_GREEN = "#0a6346"  # Verde Viaje: faixa do topo, botão e links
_BRAND_GREEN_ON = "#ffffff"  # texto sobre o Verde Viaje
_FONT = "Arial,Helvetica,sans-serif"


def _logo_url() -> str:
    """Logo da faixa verde: o de Admin master › Marca e SEO, ou o padrão."""
    try:
        from app.services.platform_branding import absolute_url, current

        custom = absolute_url(current().get("email_logo_url"))
        if custom:
            return escape(custom, quote=True)
    except Exception:  # pragma: no cover - leitura defensiva
        logger.debug("Logo dos e-mails: usando o padrão.", exc_info=True)
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
        f'<div style="background:#e6f5df;border-radius:12px;padding:14px 16px;margin:6px 0 18px;'
        f'font-size:15px;color:#0e1f17;">{highlight}</div>'
        if highlight
        else ""
    )
    link_html = (
        '<p style="margin:18px 0 0;font-size:13px;line-height:1.5;color:#5a6d62;">'
        "Se o botão não funcionar, copie e cole este link no navegador:<br>"
        f'<a href="{button_url}" style="color:{_BRAND_GREEN};word-break:break-all;">{button_url}</a></p>'
        if show_link
        else ""
    )
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#eff3ed;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#eff3ed;"><tr><td align="center" style="padding:28px 12px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:18px;overflow:hidden;font-family:{_FONT};color:#0e1f17;">
    <tr><td align="center" style="background:{_BRAND_GREEN};padding:26px 32px;">
      <img src="{_logo_url()}" alt="Roteiro Online" width="170" style="display:block;width:170px;max-width:100%;height:auto;border:0;">
    </td></tr>
    <tr><td style="padding:34px 32px 8px;">
      <p style="margin:0 0 10px;font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:{_BRAND_GREEN};font-weight:700;">{eyebrow}</p>
      <h1 style="margin:0 0 14px;font-size:25px;line-height:1.25;color:#0e1f17;">{title}</h1>
      {body_html}
      {highlight_html}
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:10px 0 4px;">
        <a href="{button_url}" style="display:inline-block;background:{_BRAND_GREEN};color:{_BRAND_GREEN_ON};text-decoration:none;font-weight:700;font-size:16px;padding:15px 34px;border-radius:999px;">{button_label}</a>
      </td></tr></table>
      {link_html}
    </td></tr>
    <tr><td style="background:#f5f8f3;border-top:1px solid #e1e8dc;padding:18px 32px;font-size:13px;line-height:1.5;color:#5a6d62;">{note_html}</td></tr>
  </table>
  <p style="max-width:560px;margin:16px auto 0;font-family:{_FONT};font-size:12px;line-height:1.6;color:#5a6d62;text-align:center;">
    Roteiro Online · Suporte: {escape(support)}<br>Você recebeu este e-mail porque há uma conta com este endereço no Roteiro Online.
  </p>
</td></tr></table>
</body></html>"""


def _plan_highlight(plan_label: str, cycle_label: str) -> str:
    return f"<b>{escape(plan_label.capitalize())}</b>" + (f" · {escape(cycle_label)}" if cycle_label else "")


def _send_system_email(key: str, *, to_email: str, values: dict, button_url: str, highlight: str | None = None) -> None:
    """Monta com os textos de Admin master › E-mails do sistema (ou o padrão) e envia."""
    from app.services.platform_branding import build_system_email

    subject, html_body, text_body = build_system_email(key, values, button_url=button_url, highlight=highlight)
    EmailClient().send_email(to_email=to_email, subject=subject, html_body=html_body, text_body=text_body)


def send_cakto_onboarding_email(
    *,
    user: "User",
    onboarding_token: "CaktoOnboardingToken",
    plan_key: str,
    cycle: str,
) -> None:
    """Dispara o e-mail de boas-vindas apos um checkout concluido na Cakto."""

    settings = get_settings()
    if not EmailClient()._is_configured():
        logger.info("SMTP nao configurado. Onboarding para %s nao sera enviado.", user.email)
        return
    password_url = f"{settings.resolved_webapp_base_url}/create-password"
    plan_label = _plan_label(plan_key)
    cycle_label = _cycle_label(cycle)
    _send_system_email(
        "boas_vindas_cakto",
        to_email=user.email,
        values={"nome": user.name or user.email, "plano": plan_label, "ciclo": cycle_label, "link": password_url},
        button_url=password_url,
        highlight=_plan_highlight(plan_label, cycle_label),
    )


def send_team_invite_email(
    *,
    to_email: str,
    invitee_name: str,
    inviter_name: str,
    agency_name: str,
    invite_url: str,
    expires_days: int = 7,
) -> None:
    if not EmailClient()._is_configured():
        logger.info("SMTP nao configurado. Convite de equipe para %s nao sera enviado.", to_email)
        return
    _send_system_email(
        "convite_equipe",
        to_email=to_email,
        values={
            "nome": invitee_name or to_email,
            "quem_convidou": inviter_name or "Administrador",
            "agencia": agency_name,
            "dias": str(expires_days),
            "link": invite_url,
        },
        button_url=invite_url,
    )


def send_checkout_welcome_email(
    *,
    to_email: str,
    name: str | None,
    plan_key: str | None,
    cycle: str | None,
    password_url: str,
) -> None:
    """Cliente novo que acabou de pagar pelo checkout (Asaas): confirma a compra e leva a definir a senha."""

    if not EmailClient()._is_configured():
        logger.info("SMTP nao configurado. Boas-vindas para %s nao serao enviadas.", to_email)
        return
    plan_label = _plan_label(plan_key)
    cycle_label = _cycle_label(cycle)
    _send_system_email(
        "boas_vindas_checkout",
        to_email=to_email,
        values={"nome": name or to_email, "plano": plan_label, "ciclo": cycle_label, "link": password_url},
        button_url=password_url,
        highlight=_plan_highlight(plan_label, cycle_label),
    )


def _validity_label(expires_minutes: int) -> str:
    hours = expires_minutes // 60
    if expires_minutes % 60 == 0 and hours:
        return f"{hours} hora{'s' if hours != 1 else ''}"
    return f"{expires_minutes} minutos"


def send_password_reset_email(*, to_email: str, name: str | None, reset_url: str, expires_minutes: int) -> None:
    if not EmailClient()._is_configured():
        logger.info("SMTP nao configurado. Redefinicao de senha para %s nao sera enviada.", to_email)
        return
    _send_system_email(
        "redefinir_senha",
        to_email=to_email,
        values={"nome": name or to_email, "validade": _validity_label(expires_minutes), "link": reset_url},
        button_url=reset_url,
    )
