"""Avisos de cobrança para os clientes (assinatura do Roteiro Online), por e-mail e WhatsApp.

Etapas:
- Fatura disponível: sai quando faltam até N dias para o vencimento (N ajustável, padrão 10). Nunca no
  mesmo dia em que a cobrança nasce (o cliente pode estar pagando no checkout naquele momento).
- 3 dias antes, no dia do vencimento, 1 e 3 dias de atraso: saem na rotina diária das 08:07.
- Pagamento confirmado: sai na hora, pelo aviso do Asaas.

Regras:
- Cada etapa sai uma vez por fatura e canal. A trava é a linha de billing_notice_sends: o envio reserva
  a linha antes de sair. Se falha, pode ser tentado de novo até 3 vezes.
- A rotina lê as faturas no Asaas na hora: fatura paga, apagada ou estornada não recebe aviso. Também
  não recebe fatura trocada por outra (renovação, nova autorização) nem de um período já pago.
- Lembretes antes do vencimento não saem para cartão de crédito nem Pix Automático (são cobrados
  sozinhos). Os de atraso saem para todos.
- No dia em que sai "Fatura disponível", os lembretes de 3 dias e do vencimento não saem juntos.
- Conta encerrada, conta interna (admin) e chave geral desligada: nada sai.
"""
from __future__ import annotations

import html
import logging
import re
import threading
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Iterable
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.billing_notice import BillingNoticeSend, BillingNoticeSettings
from app.models.subscription import Subscription
from app.models.user import User
from app.models.whatsapp import WhatsAppConnection
from app.services.asaas import AsaasAPIError, AsaasClient
from app.services.billing_account import (
    covered_by_paid,
    covered_period,
    is_paid_payment,
    mark_event_once,
    parse_date,
    pix_automatic_status,
    replaced_payment_ids,
)
from app.services.billing_operations import owner_of_payment
from app.services.company_status import ENDED_STATUSES

logger = logging.getLogger(__name__)

BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")
DAILY_RUN_AT = (8, 7)  # 08:07, horário de Brasília
MAX_ATTEMPTS = 3
DEFAULT_LEAD_DAYS = 10
MIN_LEAD_DAYS, MAX_LEAD_DAYS = 1, 60
CHANNELS = ("whatsapp", "email")
OPEN_STATUSES = frozenset({"PENDING", "OVERDUE"})
# Pagamento confirmado: avisos antigos que o Asaas reenviar não viram mensagem.
CONFIRMED_MAX_AGE_DAYS = 3
# Testes desligam para enviar na mesma linha de execução.
RUN_IN_BACKGROUND = True
# Conta criada há menos que isto: a primeira compra já tem o e-mail de boas-vindas.
NEW_ACCOUNT_GRACE = timedelta(days=2)


@dataclass(frozen=True)
class Step:
    key: str
    label: str
    description: str
    # reminder: antes do vencimento; overdue: em atraso; confirmed: pagamento recebido.
    kind: str
    button_label: str
    email_note: str


STEPS: tuple[Step, ...] = (
    Step(
        "fatura_disponivel",
        "Fatura disponível",
        "Quando faltam até {dias} dias para o vencimento.",
        "reminder",
        "Ver fatura",
        "Se você já pagou, pode desconsiderar este aviso.",
    ),
    Step(
        "lembrete_3_dias",
        "3 dias antes do vencimento",
        "Três dias antes do vencimento, às 08:07.",
        "reminder",
        "Pagar fatura",
        "Se você já pagou, pode desconsiderar este aviso.",
    ),
    Step(
        "vence_hoje",
        "No dia do vencimento",
        "No dia do vencimento, às 08:07.",
        "reminder",
        "Pagar fatura",
        "Se você já pagou, pode desconsiderar este aviso.",
    ),
    Step(
        "atraso_1_dia",
        "1 dia de atraso",
        "Um dia depois do vencimento, se a fatura continuar em aberto.",
        "overdue",
        "Pagar fatura",
        "Se você já pagou, pode desconsiderar este aviso. Precisando de ajuda, é só responder.",
    ),
    Step(
        "atraso_3_dias",
        "3 dias de atraso",
        "Três dias depois do vencimento, se a fatura continuar em aberto.",
        "overdue",
        "Pagar fatura",
        "Se você já pagou, pode desconsiderar este aviso. Precisando de ajuda, é só responder.",
    ),
    Step(
        "pagamento_confirmado",
        "Pagamento confirmado",
        "Na hora em que o Asaas confirma o pagamento.",
        "confirmed",
        "Ver comprovante",
        "Obrigado por continuar com a gente.",
    ),
)
STEP_BY_KEY = {step.key: step for step in STEPS}

VARIABLES: tuple[tuple[str, str], ...] = (
    ("nome", "Primeiro nome do cliente"),
    ("nome_completo", "Nome completo"),
    ("plano", "Plano (ex.: plano Essencial)"),
    ("valor", "Valor da fatura"),
    ("vencimento", "Data de vencimento"),
    ("link", "Link para pagar ou ver a fatura"),
    ("dias", "Dias até o vencimento ou de atraso"),
)

DEFAULT_TEMPLATES: dict[str, dict[str, str]] = {
    "fatura_disponivel": {
        "whatsapp": (
            "Olá, {{nome}}! Tudo bem?\n\n"
            "A fatura do seu {{plano}} no Roteiro Online já está disponível.\n\n"
            "*Valor:* {{valor}}\n*Vencimento:* {{vencimento}}\n\n"
            "Para pagar, é só acessar: {{link}}\n\n"
            "Qualquer dúvida, estamos por aqui. 😊"
        ),
        "email_subject": "Sua fatura do Roteiro Online está disponível",
        "email_body": (
            "Olá, {{nome}}! Tudo bem?\n\n"
            "A fatura do seu {{plano}} já está disponível.\n\n"
            "*Valor:* {{valor}}\n*Vencimento:* {{vencimento}}\n\n"
            "Você pode pagar pelo botão abaixo."
        ),
    },
    "lembrete_3_dias": {
        "whatsapp": (
            "Olá, {{nome}}! Passando para lembrar que a fatura do seu {{plano}} vence em 3 dias, "
            "em {{vencimento}}.\n\n"
            "*Valor:* {{valor}}\n\n"
            "Link para pagamento: {{link}}\n\n"
            "Se já pagou, pode desconsiderar esta mensagem. Obrigado!"
        ),
        "email_subject": "Sua fatura vence em 3 dias",
        "email_body": (
            "Olá, {{nome}}!\n\n"
            "Passando para lembrar que a fatura do seu {{plano}} vence em 3 dias, em {{vencimento}}.\n\n"
            "*Valor:* {{valor}}"
        ),
    },
    "vence_hoje": {
        "whatsapp": (
            "Olá, {{nome}}! A fatura do seu {{plano}} vence hoje ({{vencimento}}).\n\n"
            "*Valor:* {{valor}}\n\n"
            "Pague pelo link: {{link}}\n\n"
            "Se já pagou, desconsidere esta mensagem. 😊"
        ),
        "email_subject": "Sua fatura vence hoje",
        "email_body": (
            "Olá, {{nome}}!\n\n"
            "A fatura do seu {{plano}} vence hoje ({{vencimento}}).\n\n"
            "*Valor:* {{valor}}"
        ),
    },
    "atraso_1_dia": {
        "whatsapp": (
            "Olá, {{nome}}, tudo bem? Ainda não identificamos o pagamento da fatura do seu {{plano}}, "
            "que venceu ontem ({{vencimento}}).\n\n"
            "*Valor:* {{valor}}\n\n"
            "Para manter suas páginas no ar, é só pagar pelo link: {{link}}\n\n"
            "Se já pagou, desconsidere. Precisando de ajuda, é só responder esta mensagem."
        ),
        "email_subject": "Não identificamos o pagamento da sua fatura",
        "email_body": (
            "Olá, {{nome}}, tudo bem?\n\n"
            "Ainda não identificamos o pagamento da fatura do seu {{plano}}, que venceu ontem ({{vencimento}}).\n\n"
            "*Valor:* {{valor}}\n\n"
            "Para manter suas páginas no ar, é só pagar pelo botão abaixo."
        ),
    },
    "atraso_3_dias": {
        "whatsapp": (
            "Olá, {{nome}}. A fatura do seu {{plano}}, que venceu em {{vencimento}}, continua em aberto.\n\n"
            "*Valor:* {{valor}}\n\n"
            "Para não ter o acesso e as páginas suspensos, faça o pagamento pelo link: {{link}}\n\n"
            "Se precisar de ajuda ou de outra forma de pagamento, responda esta mensagem."
        ),
        "email_subject": "Sua fatura continua em aberto",
        "email_body": (
            "Olá, {{nome}}.\n\n"
            "A fatura do seu {{plano}}, que venceu em {{vencimento}}, continua em aberto.\n\n"
            "*Valor:* {{valor}}\n\n"
            "Para não ter o acesso e as páginas suspensos, faça o pagamento pelo botão abaixo."
        ),
    },
    "pagamento_confirmado": {
        "whatsapp": (
            "Olá, {{nome}}! Recebemos o pagamento de {{valor}} do seu {{plano}}. Obrigado! 🎉\n\n"
            "Seu acesso ao Roteiro Online segue normalmente."
        ),
        "email_subject": "Pagamento confirmado",
        "email_body": (
            "Olá, {{nome}}!\n\n"
            "Recebemos o pagamento de {{valor}} do seu {{plano}}. Obrigado!\n\n"
            "Seu acesso ao Roteiro Online segue normalmente."
        ),
    },
}

TEMPLATE_FIELDS = ("whatsapp", "email_subject", "email_body")


# ---------------------------------------------------------------- datas e formatos


def sao_paulo_now() -> datetime:
    return datetime.now(BRAZIL_TZ)


def sao_paulo_today() -> date:
    return sao_paulo_now().date()


def local_date(value: datetime | None) -> date:
    """Data de Brasília de um horário gravado (sem fuso = UTC)."""
    if value is None:
        return sao_paulo_today()
    aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return aware.astimezone(BRAZIL_TZ).date()


def format_brl(value: Any) -> str:
    try:
        amount = Decimal(str(value if value is not None else "0")).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        amount = Decimal("0.00")
    text = f"{amount:,.2f}"
    return f"R$ {text.replace(',', 'X').replace('.', ',').replace('X', '.')}"


def format_date_br(value: date | None) -> str:
    return value.strftime("%d/%m/%Y") if value else ""


def whatsapp_number(phone: str | None) -> str | None:
    """Número no formato da Evolution: só dígitos, com o 55 do Brasil quando faltar."""
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) in (10, 11):
        digits = f"55{digits}"
    if len(digits) < 12:
        return None
    return digits


def _plan_label(plan_key: str | None) -> str:
    from app.services.email import _plan_label as email_plan_label

    return email_plan_label(plan_key)


def first_name(name: str | None) -> str:
    parts = (name or "").strip().split()
    return parts[0] if parts else "tudo bem"


# ---------------------------------------------------------------- configuração


def get_settings_row(db: Session) -> BillingNoticeSettings:
    row = db.get(BillingNoticeSettings, 1)
    if row is None:
        row = BillingNoticeSettings(id=1, enabled=False, available_lead_days=DEFAULT_LEAD_DAYS, asaas_notifications_enabled=True)
        db.add(row)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            row = db.get(BillingNoticeSettings, 1)
        db.refresh(row)
    return row


def lead_days(settings_row: BillingNoticeSettings) -> int:
    value = int(settings_row.available_lead_days or DEFAULT_LEAD_DAYS)
    return max(MIN_LEAD_DAYS, min(MAX_LEAD_DAYS, value))


def schedule_since(settings_row: BillingNoticeSettings, today: date) -> date:
    """Dia a partir do qual os avisos valem. Sem data gravada, vale hoje (nada retroativo)."""
    return settings_row.schedule_since or today


def step_channels(settings_row: BillingNoticeSettings) -> dict[str, dict[str, bool]]:
    """Etapa → canal → ligado. Sem nada gravado, todas as etapas ligadas nos dois canais."""
    saved = settings_row.steps_json if isinstance(settings_row.steps_json, dict) else {}
    result: dict[str, dict[str, bool]] = {}
    for step in STEPS:
        current = saved.get(step.key) if isinstance(saved.get(step.key), dict) else {}
        result[step.key] = {channel: bool(current.get(channel, True)) for channel in CHANNELS}
    return result


def step_templates(settings_row: BillingNoticeSettings) -> dict[str, dict[str, str]]:
    saved = settings_row.templates_json if isinstance(settings_row.templates_json, dict) else {}
    result: dict[str, dict[str, str]] = {}
    for step in STEPS:
        current = saved.get(step.key) if isinstance(saved.get(step.key), dict) else {}
        result[step.key] = {
            name: (str(current.get(name)).strip() if current.get(name) else "") or DEFAULT_TEMPLATES[step.key][name]
            for name in TEMPLATE_FIELDS
        }
    return result


def custom_template_fields(settings_row: BillingNoticeSettings) -> dict[str, list[str]]:
    """Campos com texto próprio (diferente do padrão), por etapa."""
    saved = settings_row.templates_json if isinstance(settings_row.templates_json, dict) else {}
    result: dict[str, list[str]] = {}
    for step in STEPS:
        current = saved.get(step.key) if isinstance(saved.get(step.key), dict) else {}
        result[step.key] = [
            name
            for name in TEMPLATE_FIELDS
            if current.get(name) and str(current.get(name)).strip() != DEFAULT_TEMPLATES[step.key][name]
        ]
    return result


def clean_templates(raw: dict[str, Any] | None) -> dict[str, dict[str, str]]:
    """Guarda só o que difere do padrão: texto igual ao padrão volta a acompanhar o padrão."""
    result: dict[str, dict[str, str]] = {}
    for key, values in (raw or {}).items():
        if key not in STEP_BY_KEY or not isinstance(values, dict):
            continue
        kept = {}
        for name in TEMPLATE_FIELDS:
            text = str(values.get(name) or "").strip()
            if text and text != DEFAULT_TEMPLATES[key][name]:
                kept[name] = text[:4000]
        if kept:
            result[key] = kept
    return result


def sender_connection(db: Session, settings_row: BillingNoticeSettings) -> WhatsAppConnection | None:
    if not settings_row.whatsapp_connection_id:
        return None
    return db.get(WhatsAppConnection, settings_row.whatsapp_connection_id)


# ---------------------------------------------------------------- texto


_VAR_RE = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")


def render(template: str, context: dict[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        value = context.get(key)
        return str(value) if value is not None else match.group(0)

    return _VAR_RE.sub(replace, template or "")


def _email_body_html(text: str) -> str:
    """Texto simples → HTML: *negrito*, linha em branco abre parágrafo. Nunca vira HTML do usuário."""
    from app.services.email import _paragraph

    paragraphs = [block.strip() for block in re.split(r"\n\s*\n", text or "") if block.strip()]
    parts = []
    for block in paragraphs:
        escaped = html.escape(block)
        escaped = re.sub(r"\*([^*\n]+)\*", r"<b>\1</b>", escaped)
        parts.append(_paragraph(escaped.replace("\n", "<br>")))
    return "".join(parts)


def build_email(step_key: str, templates: dict[str, str], context: dict[str, Any]) -> tuple[str, str, str]:
    """(assunto, html, texto) do e-mail da etapa."""
    from app.services.email import _email_layout

    step = STEP_BY_KEY[step_key]
    subject = render(templates["email_subject"], context).strip() or step.label
    body = render(templates["email_body"], context)
    link = str(context.get("link") or "").strip() or _invoices_url()
    html_body = _email_layout(
        eyebrow="Roteiro Online · Fatura",
        title=html.escape(subject),
        body_html=_email_body_html(body),
        button_url=html.escape(link, quote=True),
        button_label=step.button_label,
        note_html=html.escape(step.email_note),
    )
    text_body = f"{body}\n\n{step.button_label}: {link}"
    return subject, html_body, text_body


def _invoices_url() -> str:
    return f"{get_settings().resolved_webapp_base_url}/admin/agency/invoices"


def build_context(user: User | None, payment: dict[str, Any], today: date | None = None) -> dict[str, Any]:
    today = today or sao_paulo_today()
    due = parse_date(payment.get("dueDate"))
    plan = user.subscription.plan if user is not None and user.subscription is not None else None
    link = (
        str(payment.get("transactionReceiptUrl") or "").strip()
        if is_paid_payment(payment)
        else ""
    ) or str(payment.get("invoiceUrl") or payment.get("bankSlipUrl") or "").strip()
    days = abs((due - today).days) if due else 0
    return {
        "nome": first_name(user.name if user else None),
        "nome_completo": (user.name if user else "") or "",
        "plano": _plan_label(plan),
        "valor": format_brl(payment.get("value")),
        "vencimento": format_date_br(due),
        "link": link or _invoices_url(),
        "dias": str(days),
    }


SAMPLE_CONTEXT = {
    "nome": "Maria",
    "nome_completo": "Maria Souza",
    "plano": "plano Essencial",
    "valor": "R$ 97,00",
    "vencimento": "10/12/2026",
    "link": "https://www.asaas.com/i/exemplo",
    "dias": "3",
}


# ---------------------------------------------------------------- envio


def send_whatsapp(db: Session, settings_row: BillingNoticeSettings, number: str, text: str) -> None:
    from app.services.evolution import EvolutionService

    connection = sender_connection(db, settings_row)
    if connection is None:
        raise RuntimeError("Nenhuma conexão de WhatsApp escolhida para os avisos.")
    if str(connection.status or "").lower() != "connected":
        raise RuntimeError(f"A conexão de WhatsApp “{connection.name}” não está conectada.")
    EvolutionService().send_text_target(target=number, text=text, instance_name=connection.instance_name)


def send_email(to_email: str, subject: str, html_body: str, text_body: str) -> None:
    from app.services.email import EmailClient

    EmailClient().send_email(to_email=to_email, subject=subject, html_body=html_body, text_body=text_body, raise_errors=True)


def deliver(db: Session, settings_row: BillingNoticeSettings, step_key: str, channel: str, recipient: str, context: dict[str, Any]) -> None:
    """Envia agora; levanta erro quando não sai."""
    templates = step_templates(settings_row)[step_key]
    if channel == "whatsapp":
        send_whatsapp(db, settings_row, recipient, render(templates["whatsapp"], context))
    elif channel == "email":
        subject, html_body, text_body = build_email(step_key, templates, context)
        send_email(recipient, subject, html_body, text_body)
    else:  # pragma: no cover - canal desconhecido
        raise ValueError(f"Canal desconhecido: {channel}")


def recipient_for(user: User, channel: str) -> str | None:
    if channel == "whatsapp":
        return whatsapp_number(user.whatsapp)
    email = (user.email or "").strip()
    return email or None


def claim(
    db: Session,
    *,
    payment_id: str,
    step: str,
    channel: str,
    user_id: int | None,
    recipient: str | None,
    due_date: date | None,
    context: dict[str, Any],
) -> BillingNoticeSend | None:
    """Reserva o envio antes de sair. None quando já saiu, está saindo, foi cancelado ou esgotou as
    tentativas. A reserva é atômica no banco: dois processos ao mesmo tempo não mandam em dobro."""
    row = BillingNoticeSend(
        payment_id=payment_id,
        step=step,
        channel=channel,
        status="sending",
        attempts=1,
        user_id=user_id,
        recipient=recipient,
        due_date=due_date,
        context_json=context,
    )
    db.add(row)
    try:
        db.commit()
        return row
    except IntegrityError:
        db.rollback()
    updated = (
        db.query(BillingNoticeSend)
        .filter(
            BillingNoticeSend.payment_id == payment_id,
            BillingNoticeSend.step == step,
            BillingNoticeSend.channel == channel,
            BillingNoticeSend.status == "failed",
            BillingNoticeSend.attempts < MAX_ATTEMPTS,
        )
        .update(
            {
                BillingNoticeSend.status: "sending",
                BillingNoticeSend.attempts: BillingNoticeSend.attempts + 1,
                BillingNoticeSend.recipient: recipient,
                BillingNoticeSend.context_json: context,
                BillingNoticeSend.updated_at: datetime.now(timezone.utc),
            },
            synchronize_session=False,
        )
    )
    db.commit()
    if not updated:
        return None
    return (
        db.query(BillingNoticeSend)
        .filter(
            BillingNoticeSend.payment_id == payment_id,
            BillingNoticeSend.step == step,
            BillingNoticeSend.channel == channel,
        )
        .first()
    )


def _finish(db: Session, row: BillingNoticeSend, error: str | None) -> None:
    row.status = "failed" if error else "sent"
    row.error = (error or None) and error[:1000]
    row.sent_at = None if error else datetime.now(timezone.utc)
    db.add(row)
    db.commit()


def send_claimed(db: Session, settings_row: BillingNoticeSettings, row: BillingNoticeSend) -> bool:
    try:
        deliver(db, settings_row, row.step, row.channel, row.recipient or "", dict(row.context_json or {}))
    except Exception as exc:  # noqa: BLE001 - qualquer falha fica no histórico
        logger.warning("Aviso de cobrança não saiu (%s/%s/%s): %s", row.payment_id, row.step, row.channel, exc)
        _finish(db, row, str(exc) or exc.__class__.__name__)
        return False
    _finish(db, row, None)
    return True


def notify(
    db: Session,
    settings_row: BillingNoticeSettings,
    *,
    user: User,
    payment: dict[str, Any],
    step: str,
    channels: Iterable[str],
    context: dict[str, Any],
) -> dict[str, str]:
    """Reserva e envia a etapa em cada canal. Devolve canal → resultado (sent, failed, skipped)."""
    payment_id = str(payment.get("id") or "")
    due = parse_date(payment.get("dueDate"))
    results: dict[str, str] = {}
    for channel in channels:
        recipient = recipient_for(user, channel)
        if not recipient:
            results[channel] = "skipped"
            continue
        row = claim(
            db,
            payment_id=payment_id,
            step=step,
            channel=channel,
            user_id=user.id,
            recipient=recipient,
            due_date=due,
            context=context,
        )
        if row is None:
            results[channel] = "skipped"
            continue
        results[channel] = "sent" if send_claimed(db, settings_row, row) else "failed"
    return results


# ---------------------------------------------------------------- o que cada fatura recebe


@dataclass
class PlannedNotice:
    date: date
    step: str
    payment: dict[str, Any]
    user: User
    # canal → motivo de não sair (None: sai)
    channels: dict[str, str | None] = field(default_factory=dict)
    # motivo de a etapa inteira não sair (None: sai nos canais sem motivo)
    reason: str | None = None


def _payment_kind_reason(db: Session, user: User, payment: dict[str, Any], cache: dict[int, str | None]) -> str | None:
    """Lembretes antes do vencimento não fazem sentido para quem é cobrado sozinho."""
    if str(payment.get("billingType") or "").upper() == "CREDIT_CARD":
        return "Cartão de crédito: cobrado automaticamente"
    if user.id not in cache:
        try:
            cache[user.id] = pix_automatic_status(db, user)
        except Exception:  # pragma: no cover - leitura defensiva
            cache[user.id] = None
    if cache[user.id] == "ACTIVE":
        return "Pix Automático: debitado automaticamente"
    return None


def available_date(payment: dict[str, Any], lead: int) -> date | None:
    """Dia em que "Fatura disponível" sai: N dias antes do vencimento, nunca no dia em que a cobrança
    nasceu."""
    due = parse_date(payment.get("dueDate"))
    if due is None:
        return None
    planned = due - timedelta(days=lead)
    created = parse_date(payment.get("dateCreated"))
    if created is not None:
        planned = max(planned, created + timedelta(days=1))
    return planned if planned <= due else None


def steps_on(
    payment: dict[str, Any],
    day: date,
    lead: int,
    today: date,
    available_done: bool = False,
    since: date | None = None,
) -> list[str]:
    """Etapas que a fatura recebe no dia `day`. `available_done`: "Fatura disponível" já saiu (ou foi
    cancelada) antes. `since`: dia em que os avisos foram ligados (ou o prazo mudou); nada que deveria
    ter saído antes dele sai agora (sem envio retroativo)."""
    due = parse_date(payment.get("dueDate"))
    if due is None:
        return []
    created = parse_date(payment.get("dateCreated"))
    if created is not None and day <= created:
        # No dia em que a cobrança nasce o cliente pode estar pagando no checkout: nada sai.
        return []
    result: list[str] = []
    available = available_date(payment, lead)
    # "Fatura disponível" que ficou para trás (rotina parada, fatura vista depois) sai no próximo dia
    # da rotina, até o vencimento.
    if available is not None and since is not None and available < since:
        # Deveria ter saído antes de os avisos serem ligados: não sai atrasada.
        available = None
    if available is not None and (
        available == day or (not available_done and day == today and available < day <= due)
    ):
        result.append("fatura_disponivel")
    offset = (due - day).days
    if offset == 3:
        result.append("lembrete_3_dias")
    elif offset == 0:
        result.append("vence_hoje")
    elif offset == -1:
        result.append("atraso_1_dia")
    elif offset == -3:
        result.append("atraso_3_dias")
    if "fatura_disponivel" in result:
        # No dia da "Fatura disponível", os lembretes não saem juntos.
        result = [key for key in result if key not in {"lembrete_3_dias", "vence_hoje"}]
    return result


def _account_reason(user: User | None) -> str | None:
    if user is None:
        return "Fatura sem conta no Roteiro Online"
    if user.is_superuser:
        return "Conta interna"
    sub: Subscription | None = user.subscription
    if sub is None:
        return "Conta sem assinatura"
    if str(sub.status or "").strip().lower() in ENDED_STATUSES:
        return "Assinatura encerrada"
    return None


class PaymentScan:
    """Faturas em aberto no Asaas e quem é o dono, com as consultas guardadas para a rodada."""

    def __init__(self, db: Session, client: AsaasClient) -> None:
        self.db = db
        self.client = client
        self._owners: dict[str, User | None] = {}
        self._paid_periods: dict[int, list[tuple[date, date]]] = {}
        self._pix: dict[int, str | None] = {}

    def open_payments(self, start: date, end: date) -> list[dict[str, Any]]:
        rows: dict[str, dict[str, Any]] = {}
        for status in sorted(OPEN_STATUSES):
            offset = 0
            while True:
                payload = self.client.list_payments(
                    status=status,
                    limit=100,
                    offset=offset,
                    **{"dueDate[ge]": start.isoformat(), "dueDate[le]": end.isoformat()},
                ) or {}
                batch = [item for item in payload.get("data") or [] if isinstance(item, dict)]
                for item in batch:
                    if item.get("id") and item.get("deleted") is not True:
                        rows[str(item["id"])] = item
                if len(batch) < 100 or offset >= 5000:
                    break
                offset += 100
        return list(rows.values())

    def owner(self, payment: dict[str, Any]) -> User | None:
        payment_id = str(payment.get("id") or "")
        if payment_id not in self._owners:
            self._owners[payment_id] = owner_of_payment(self.db, payment)
        return self._owners[payment_id]

    def paid_periods(self, user: User) -> list[tuple[date, date]]:
        if user.id in self._paid_periods:
            return self._paid_periods[user.id]
        periods: list[tuple[date, date]] = []
        sub = user.subscription
        customer = sub.asaas_customer_id if sub else None
        if customer:
            try:
                payload = self.client.list_payments(customer=customer, limit=100) or {}
                cycle = sub.billing_cycle if sub else None
                for item in payload.get("data") or []:
                    if isinstance(item, dict) and is_paid_payment(item):
                        period = covered_period(parse_date(item.get("dueDate")), cycle)
                        if period:
                            periods.append(period)
            except AsaasAPIError as exc:  # noqa: BLE001
                logger.warning("Não foi possível ler os pagamentos do cliente %s: %s", customer, exc)
        self._paid_periods[user.id] = periods
        return periods

    def payment_reason(self, user: User | None, payment: dict[str, Any], replaced: set[str]) -> str | None:
        reason = _account_reason(user)
        if reason:
            return reason
        if str(payment.get("id")) in replaced:
            return "Fatura trocada por outra"
        if covered_by_paid(parse_date(payment.get("dueDate")), self.paid_periods(user)):
            return "Período já pago em outra fatura"
        return None


def plan_notices(
    db: Session,
    settings_row: BillingNoticeSettings,
    scan: PaymentScan,
    payments: list[dict[str, Any]],
    days: Iterable[date],
    today: date,
) -> list[PlannedNotice]:
    lead = lead_days(settings_row)
    since = schedule_since(settings_row, today)
    channels_on = step_channels(settings_row)
    replaced = replaced_payment_ids(db, [str(item.get("id") or "") for item in payments])
    connection = sender_connection(db, settings_row)
    whatsapp_problem = None
    if connection is None:
        whatsapp_problem = "Nenhuma conexão de WhatsApp escolhida"
    elif str(connection.status or "").lower() != "connected":
        whatsapp_problem = "Conexão de WhatsApp desconectada"
    day_list = list(days)
    payment_ids = [str(item.get("id") or "") for item in payments]
    # "Fatura disponível" que já saiu (ou foi cancelada) num dia anterior: não sai de novo e não
    # segura os lembretes de hoje.
    available_done = {
        payment_id
        for payment_id, created_at in db.query(BillingNoticeSend.payment_id, BillingNoticeSend.created_at)
        .filter(
            BillingNoticeSend.payment_id.in_(payment_ids or [""]),
            BillingNoticeSend.step == "fatura_disponivel",
            BillingNoticeSend.status != "failed",
        )
        .all()
        if local_date(created_at) < today
    }
    planned: list[PlannedNotice] = []
    for payment in payments:
        status = str(payment.get("status") or "").upper()
        if status not in OPEN_STATUSES:
            continue
        due = parse_date(payment.get("dueDate"))
        if due is None:
            continue
        done = str(payment.get("id")) in available_done
        steps_by_day = [(day, steps_on(payment, day, lead, today, done, since)) for day in day_list]
        if not any(steps for _day, steps in steps_by_day):
            continue
        user = scan.owner(payment)
        if user is None:
            continue
        payment_reason = scan.payment_reason(user, payment, replaced)
        for day, steps in steps_by_day:
            for step_key in steps:
                step = STEP_BY_KEY[step_key]
                notice = PlannedNotice(date=day, step=step_key, payment=payment, user=user)
                if payment_reason:
                    notice.reason = payment_reason
                elif step.kind == "reminder":
                    notice.reason = _payment_kind_reason(db, user, payment, scan._pix)
                for channel in CHANNELS:
                    if not channels_on[step_key][channel]:
                        notice.channels[channel] = "Etapa desligada neste canal"
                    elif not recipient_for(user, channel):
                        notice.channels[channel] = "Sem WhatsApp cadastrado" if channel == "whatsapp" else "Sem e-mail cadastrado"
                    elif channel == "whatsapp" and whatsapp_problem:
                        notice.channels[channel] = whatsapp_problem
                    else:
                        notice.channels[channel] = None
                planned.append(notice)
    return planned


# ---------------------------------------------------------------- rotina diária


def asaas_client() -> AsaasClient | None:
    cfg = get_settings()
    if not cfg.asaas_api_key:
        return None
    return AsaasClient(cfg.asaas_api_key, cfg.asaas_base_url)


def run_daily(db: Session, *, today: date | None = None, client: AsaasClient | None = None) -> dict[str, Any]:
    """Envia as etapas do dia. Pode rodar de novo no mesmo dia: a trava não deixa repetir."""
    settings_row = get_settings_row(db)
    summary: dict[str, Any] = {"sent": 0, "failed": 0, "skipped": 0, "payments": 0}
    if not settings_row.enabled:
        summary["disabled"] = True
        return summary
    client = client or asaas_client()
    if client is None:
        raise RuntimeError("A chave da API Asaas não está configurada no servidor.")
    today = today or sao_paulo_today()
    lead = lead_days(settings_row)
    scan = PaymentScan(db, client)
    payments = scan.open_payments(today - timedelta(days=3), today + timedelta(days=lead))
    summary["payments"] = len(payments)
    for notice in plan_notices(db, settings_row, scan, payments, [today], today):
        if notice.reason:
            summary["skipped"] += 1
            continue
        channels = [channel for channel, reason in notice.channels.items() if reason is None]
        if not channels:
            summary["skipped"] += 1
            continue
        context = build_context(notice.user, notice.payment, today)
        for result in notify(
            db, settings_row, user=notice.user, payment=notice.payment, step=notice.step, channels=channels, context=context
        ).values():
            summary[result] = summary.get(result, 0) + 1
    logger.info("Avisos de cobrança do dia %s: %s", today, summary)
    return summary


def retry_failed(db: Session, *, client: AsaasClient | None = None, now: datetime | None = None) -> int:
    """Tenta de novo, depois de 30 minutos, o que falhou nas últimas 20 horas (até 3 tentativas).
    Lembrete ou atraso só sai de novo se a fatura continuar em aberto no Asaas."""
    settings_row = get_settings_row(db)
    if not settings_row.enabled:
        return 0
    now = now or datetime.now(timezone.utc)
    rows = (
        db.query(BillingNoticeSend)
        .filter(
            BillingNoticeSend.status == "failed",
            BillingNoticeSend.attempts < MAX_ATTEMPTS,
            BillingNoticeSend.updated_at <= now - timedelta(minutes=30),
            BillingNoticeSend.created_at >= now - timedelta(hours=20),
        )
        .limit(200)
        .all()
    )
    if not rows:
        return 0
    client = client or asaas_client()
    sent = 0
    for row in rows:
        if STEP_BY_KEY.get(row.step) is None:
            continue
        if STEP_BY_KEY[row.step].kind != "confirmed" and client is not None:
            try:
                payment = client.get_payment(row.payment_id) or {}
            except AsaasAPIError:
                continue
            if payment.get("deleted") is True or str(payment.get("status") or "").upper() not in OPEN_STATUSES:
                row.status = "cancelled"
                row.error = "A fatura não está mais em aberto no Asaas."
                db.add(row)
                db.commit()
                continue
        if resend(db, row, manual=False):
            sent += 1
    return sent


def resend(db: Session, row: BillingNoticeSend, *, manual: bool) -> bool:
    """Envia de novo um registro que falhou (ou travou em "enviando"). Manual ignora o limite de
    tentativas."""
    settings_row = get_settings_row(db)
    stuck_before = datetime.now(timezone.utc) - timedelta(minutes=10)
    filters = [BillingNoticeSend.id == row.id]
    allowed = ["failed"]
    if manual:
        allowed.append("sending")
    query = db.query(BillingNoticeSend).filter(*filters, BillingNoticeSend.status.in_(allowed))
    if not manual:
        query = query.filter(BillingNoticeSend.attempts < MAX_ATTEMPTS)
    else:
        query = query.filter(
            (BillingNoticeSend.status == "failed") | (BillingNoticeSend.updated_at <= stuck_before)
        )
    updated = query.update(
        {
            BillingNoticeSend.status: "sending",
            BillingNoticeSend.attempts: BillingNoticeSend.attempts + 1,
            BillingNoticeSend.updated_at: datetime.now(timezone.utc),
        },
        synchronize_session=False,
    )
    db.commit()
    if not updated:
        return False
    db.refresh(row)
    return send_claimed(db, settings_row, row)


def daily_due(now: datetime | None = None) -> bool:
    current = (now or sao_paulo_now()).astimezone(BRAZIL_TZ)
    return (current.hour, current.minute) >= DAILY_RUN_AT


def hourly_tick(session_factory: Callable[[], Session], now: datetime | None = None) -> None:
    """Chamado pela rotina de hora em hora: roda o dia uma vez (depois das 08:07) e refaz falhas."""
    db = session_factory()
    try:
        settings_row = get_settings_row(db)
        if not settings_row.enabled:
            return
        current = (now or sao_paulo_now()).astimezone(BRAZIL_TZ)
        if daily_due(current) and mark_event_once(
            db,
            f"billing_notices_daily:{current.date().isoformat()}",
            "BILLING_NOTICES_DAILY",
            {"started_at": current.isoformat()},
        ):
            try:
                run_daily(db, today=current.date())
            except Exception:
                logger.exception("Erro na rotina diária dos avisos de cobrança")
        try:
            retry_failed(db)
        except Exception:
            logger.exception("Erro ao tentar de novo os avisos de cobrança")
    finally:
        db.close()


# ---------------------------------------------------------------- pagamento confirmado (webhook)


def _confirmed_recently(payment: dict[str, Any], today: date) -> bool:
    paid_on = parse_date(payment.get("paymentDate") or payment.get("confirmedDate") or payment.get("clientPaymentDate"))
    if paid_on is None:
        return True
    return (today - paid_on).days <= CONFIRMED_MAX_AGE_DAYS


def payment_confirmed(db: Session, payment: dict[str, Any], *, now: datetime | None = None) -> dict[str, str]:
    settings_row = db.get(BillingNoticeSettings, 1)
    if settings_row is None or not settings_row.enabled or not payment.get("id") or not is_paid_payment(payment):
        return {}
    today = (now or sao_paulo_now()).astimezone(BRAZIL_TZ).date()
    if not _confirmed_recently(payment, today):
        return {}
    paid_on = parse_date(payment.get("paymentDate") or payment.get("confirmedDate") or payment.get("clientPaymentDate"))
    if paid_on is not None and paid_on < schedule_since(settings_row, today):
        # Pago antes de os avisos serem ligados: não manda confirmação retroativa.
        return {}
    user = owner_of_payment(db, payment)
    if user is None or user.is_superuser or user.subscription is None:
        return {}
    created = user.created_at
    if created is not None:
        created_aware = created if created.tzinfo else created.replace(tzinfo=timezone.utc)
        if (now or datetime.now(timezone.utc)) - created_aware < NEW_ACCOUNT_GRACE:
            # Primeira compra: já recebe o e-mail de boas-vindas.
            return {}
    channels_on = step_channels(settings_row)["pagamento_confirmado"]
    channels = [channel for channel in CHANNELS if channels_on[channel]]
    if not channels:
        return {}
    context = build_context(user, payment, today)
    return notify(db, settings_row, user=user, payment=payment, step="pagamento_confirmado", channels=channels, context=context)


def schedule_payment_event(payload: dict[str, Any]) -> None:
    """Depois do webhook do Asaas: o envio vai em segundo plano para não segurar a resposta."""
    event = str(payload.get("event") or "").upper()
    payment = payload.get("payment")
    if event not in {"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"} or not isinstance(payment, dict):
        return

    def run() -> None:
        from app.db import session as db_session

        db = db_session.SessionLocal()
        try:
            payment_confirmed(db, payment)
        except Exception:
            logger.exception("Erro no aviso de pagamento confirmado")
        finally:
            db.close()

    if RUN_IN_BACKGROUND:
        threading.Thread(target=run, daemon=True).start()
    else:
        run()


# ---------------------------------------------------------------- avisos do Asaas


def asaas_notifications_disabled() -> bool:
    """Para os clientes novos do Asaas: segue a chave da tela. Sem banco, mantém os avisos do Asaas."""
    try:
        from app.db import session as db_session

        db = db_session.SessionLocal()
        try:
            row = db.get(BillingNoticeSettings, 1)
            return bool(row is not None and not row.asaas_notifications_enabled)
        finally:
            db.close()
    except Exception:  # pragma: no cover - leitura defensiva
        return False


def apply_asaas_notifications(db: Session, enabled: bool, client: AsaasClient | None = None) -> dict[str, int]:
    """Liga ou desliga os avisos do Asaas em todos os clientes que temos."""
    client = client or asaas_client()
    if client is None:
        raise RuntimeError("A chave da API Asaas não está configurada no servidor.")
    customer_ids = {
        row[0]
        for row in db.query(Subscription.asaas_customer_id).filter(Subscription.asaas_customer_id.isnot(None)).all()
        if row[0]
    }
    result = {"updated": 0, "failed": 0}
    for customer_id in sorted(customer_ids):
        try:
            client.update_customer(customer_id, {"notificationDisabled": not enabled})
            result["updated"] += 1
        except Exception as exc:  # noqa: BLE001
            result["failed"] += 1
            logger.warning("Não foi possível ajustar os avisos do Asaas do cliente %s: %s", customer_id, exc)
    logger.info("Avisos do Asaas %s: %s", "ligados" if enabled else "desligados", result)
    return result


def apply_asaas_notifications_in_background(enabled: bool) -> None:
    def run() -> None:
        from app.db import session as db_session

        db = db_session.SessionLocal()
        try:
            apply_asaas_notifications(db, enabled)
        except Exception:
            logger.exception("Erro ao ajustar os avisos do Asaas nos clientes")
        finally:
            db.close()

    threading.Thread(target=run, daemon=True).start()


# ---------------------------------------------------------------- próximos envios (tela)


def upcoming(db: Session, *, days: int = 7, client: AsaasClient | None = None, today: date | None = None) -> dict[str, Any]:
    """O que a rotina vai mandar de hoje até `days` dias, e por que cada aviso não sai. Não envia."""
    settings_row = get_settings_row(db)
    client = client or asaas_client()
    if client is None:
        raise RuntimeError("A chave da API Asaas não está configurada no servidor.")
    today = today or sao_paulo_today()
    days = max(1, min(30, int(days)))
    lead = lead_days(settings_row)
    scan = PaymentScan(db, client)
    payments = scan.open_payments(today - timedelta(days=3), today + timedelta(days=days + lead))
    day_list = [today + timedelta(days=offset) for offset in range(days + 1)]
    notices = plan_notices(db, settings_row, scan, payments, day_list, today)
    ids = list({str(n.payment.get("id")) for n in notices}) or [""]
    existing = {
        (row.payment_id, row.step, row.channel): row
        for row in db.query(BillingNoticeSend).filter(BillingNoticeSend.payment_id.in_(ids)).all()
    }
    ran_today = daily_ran(db, today)
    items = []
    for notice in sorted(notices, key=lambda n: (n.date, parse_date(n.payment.get("dueDate")) or n.date, n.user.name or "")):
        payment_id = str(notice.payment.get("id"))
        channels = []
        for channel in CHANNELS:
            row = existing.get((payment_id, notice.step, channel))
            if row is not None:
                state, reason = row.status, row.error
            elif notice.reason:
                state, reason = "skipped", notice.reason
            elif notice.channels.get(channel):
                state, reason = "skipped", notice.channels[channel]
            elif not settings_row.enabled:
                state, reason = "off", "Avisos desligados na chave geral"
            elif notice.date == today and ran_today:
                state, reason = "skipped", "A rotina de hoje já rodou"
            else:
                state, reason = "scheduled", None
            channels.append({"channel": channel, "state": state, "reason": reason, "send_id": row.id if row else None})
        items.append(
            {
                "date": notice.date.isoformat(),
                "step": notice.step,
                "step_label": STEP_BY_KEY[notice.step].label,
                "payment_id": payment_id,
                "user_id": notice.user.id,
                "name": notice.user.name,
                "email": notice.user.email,
                "phone": notice.user.whatsapp,
                "value": float(notice.payment.get("value") or 0),
                "due_date": notice.payment.get("dueDate"),
                "billing_type": notice.payment.get("billingType"),
                "invoice_url": notice.payment.get("invoiceUrl"),
                "reason": notice.reason,
                "channels": channels,
            }
        )
    return {
        "today": today.isoformat(),
        "days": days,
        "enabled": bool(settings_row.enabled),
        "ran_today": ran_today,
        "items": items,
    }


def daily_ran(db: Session, day: date) -> bool:
    from app.models.asaas import AsaasEventLog

    return (
        db.query(AsaasEventLog.id).filter(AsaasEventLog.event_id == f"billing_notices_daily:{day.isoformat()}").first()
        is not None
    )


def cancel_planned(db: Session, *, payment_id: str, step: str, channel: str, user_id: int | None, due_date: date | None) -> bool:
    """Cancela um aviso que ainda não saiu. False se já saiu ou está saindo."""
    if step not in STEP_BY_KEY or channel not in CHANNELS:
        raise ValueError("Etapa ou canal inválido.")
    row = (
        db.query(BillingNoticeSend)
        .filter(BillingNoticeSend.payment_id == payment_id, BillingNoticeSend.step == step, BillingNoticeSend.channel == channel)
        .first()
    )
    if row is None:
        db.add(
            BillingNoticeSend(
                payment_id=payment_id,
                step=step,
                channel=channel,
                status="cancelled",
                attempts=0,
                user_id=user_id,
                due_date=due_date,
                error="Cancelado no Admin master",
            )
        )
        try:
            db.commit()
            return True
        except IntegrityError:
            db.rollback()
            return False
    if row.status not in {"failed", "cancelled"}:
        return False
    row.status = "cancelled"
    row.error = "Cancelado no Admin master"
    db.add(row)
    db.commit()
    return True


def reactivate_planned(db: Session, *, payment_id: str, step: str, channel: str) -> bool:
    deleted = (
        db.query(BillingNoticeSend)
        .filter(
            BillingNoticeSend.payment_id == payment_id,
            BillingNoticeSend.step == step,
            BillingNoticeSend.channel == channel,
            BillingNoticeSend.status == "cancelled",
        )
        .delete(synchronize_session=False)
    )
    db.commit()
    return bool(deleted)
