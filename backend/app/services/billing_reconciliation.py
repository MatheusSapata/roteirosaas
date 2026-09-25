"""Read-only reconciliation; local renewal expectations never become confirmed debts."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from time import monotonic
from typing import Any, Callable
from zoneinfo import ZoneInfo

import httpx

from app.services.asaas import AsaasAPIError, AsaasClient

PAID = {"RECEIVED", "CONFIRMED", "RECEIVED_IN_CASH"}
OPEN = {"PENDING", "OVERDUE", "CREDIT_CARD_CAPTURE_REFUSED"}


def resource_id(value: Any) -> str:
    return str(value.get("id") or "") if isinstance(value, dict) else str(value or "")


def as_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value or "")[:10])
    except ValueError:
        return None


def money(value: Any) -> float:
    try:
        amount = Decimal(str(value or 0))
        return float(amount.quantize(Decimal("0.01"))) if amount.is_finite() else 0.0
    except (InvalidOperation, ValueError):
        return 0.0


def payment_method(value: Any) -> str:
    value = str(value or "UNDEFINED").upper()
    return {"CARD": "CREDIT_CARD", "PIX_AUTOMATIC": "PIX", "PIX-AUTOMATIC": "PIX"}.get(value, value)


def collect_pages(fetch: Callable, params: dict, deadline: float) -> dict:
    """Keep partial results visible and reject nonadvancing pagination."""
    rows: dict[str, dict] = {}
    offset = 0
    try:
        while monotonic() < deadline:
            payload = fetch(limit=100, offset=offset, **params)
            data = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(data, list) or any(not isinstance(row, dict) or not row.get("id") for row in data):
                return {"data": list(rows.values()), "complete": False, "error": "Resposta inesperada do Asaas."}
            previous = len(rows)
            rows.update({resource_id(row): row for row in data})
            more = payload.get("hasMore")
            if more is False or (more is None and len(data) < 100):
                return {"data": list(rows.values()), "complete": True, "error": None}
            if not data or len(rows) == previous:
                return {"data": list(rows.values()), "complete": False, "error": "Paginação sem avanço; revise o período."}
            offset += len(data)
    except (AsaasAPIError, httpx.HTTPError) as exc:
        # Expose known error codes, never provider payloads or sensitive account data.
        payload = exc.args[0] if exc.args and isinstance(exc.args[0], dict) else {}
        errors = payload.get("errors")
        invalid = isinstance(errors, list) and any(isinstance(e, dict) and e.get("code") == "invalid_access_token" for e in errors)
        message = "Chave Asaas inválida para o ambiente configurado. Atualize ASAAS_API_KEY no servidor." if invalid else "Falha na consulta. Confira conexão, ambiente e permissões de leitura da chave Asaas."
        return {"data": list(rows.values()), "complete": False, "error": message}
    return {"data": list(rows.values()), "complete": False, "error": "Tempo de consulta excedido. Restrinja o período e atualize."}


def fetch_remote(client: AsaasClient, start: date | None, end: date) -> dict:
    params = {"dueDate[le]": end.isoformat()}
    if start:
        params["dueDate[ge]"] = start.isoformat()
    deadline = monotonic() + 85
    sources = {
        "payments": (client.list_payments, params),
        "subscriptions": (client.list_subscriptions, {}),
        "authorizations": (client.list_pix_automatic_authorizations, {}),
        "instructions": (client.list_pix_automatic_payment_instructions, {}),
    }
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {key: pool.submit(collect_pages, fetch, filters, deadline) for key, (fetch, filters) in sources.items()}
        return {key: job.result() for key, job in jobs.items()}


def reconcile(remote: dict, local: list[dict], checkouts: list[dict], *, today: date,
              start: date | None, end: date) -> dict:
    subs = {resource_id(s): s for s in remote["subscriptions"]["data"]}
    auths = {resource_id(a): a for a in remote["authorizations"]["data"]}
    auths_by_customer: dict[str, list] = {}
    for auth in auths.values():
        customer = resource_id(auth.get("customerId") or auth.get("customer"))
        if customer:
            auths_by_customer.setdefault(customer, []).append({
                "id": resource_id(auth), "status": auth.get("status"),
                "creation_mode": auth.get("paymentCreationMode") or "UNKNOWN",
            })
    local_by_remote = {s["asaas_subscription_id"]: s for s in local if s.get("asaas_subscription_id") and s["provider"] == "asaas"}
    local_by_user = {s["user_id"]: s for s in local if s["provider"] == "asaas"}
    sessions_by_token = {s["token"]: s for s in checkouts}
    sessions_by_payment = {s["asaas_payment_id"]: s for s in checkouts if s.get("asaas_payment_id")}
    sessions_by_auth, latest_by_user = {}, {}
    for session in checkouts:
        if session.get("user_id") and session.get("status", "paid") == "paid":
            latest_by_user.setdefault(session["user_id"], session)
        aid = session["metadata"].get("asaas_pix_automatic_authorization_id")
        if aid:
            sessions_by_auth.setdefault(aid, session)
    instructions_by_payment: dict[str, list] = {}
    for instruction in remote["instructions"]["data"]:
        pid = resource_id(instruction.get("paymentId") or instruction.get("payment"))
        if pid:
            instructions_by_payment.setdefault(pid, []).append(instruction)

    def authorization_id(obj: dict) -> str:
        return resource_id(obj.get("pixAutomaticAuthorizationId") or obj.get("pixAutomaticAuthorization") or obj.get("authorization"))

    def pix_info(aid: str, method: str, metadata: dict, instructions: list, linked: bool) -> dict:
        auth = auths.get(aid, {})
        is_pix = method == "PIX" or bool(aid)
        known_missing = all(remote[key]["complete"] for key in ("authorizations", "instructions", "subscriptions")) and not aid
        status = str(auth.get("status") or ("MISSING" if known_missing and is_pix else "UNKNOWN"))
        return {
            "pix_kind": ("automatic" if linked else "unverified" if aid else "ordinary" if known_missing else "unknown") if is_pix else "not_pix",
            "authorization_id": aid or None, "authorization_status": status if is_pix else "NOT_APPLICABLE",
            "local_authorization_status": metadata.get("asaas_pix_automatic_authorization_status"),
            "creation_mode": str(auth.get("paymentCreationMode") or "UNKNOWN") if is_pix else "NOT_APPLICABLE",
            "retry_policy": auth.get("retryPolicy"),
            "instructions": [{"id": resource_id(i), "status": i.get("status"), "due_date": i.get("dueDate"),
                              "refusal_reason": i.get("refusalReason")} for i in instructions],
        }

    rows = []
    for payment in remote["payments"]["data"]:
        due = as_date(payment.get("dueDate"))
        if not due or due > end or (start and due < start) or payment.get("deleted"):
            continue
        pid, sid = resource_id(payment), resource_id(payment.get("subscription"))
        subscription = subs.get(sid, {})
        instructions = instructions_by_payment.get(pid, [])
        aid = authorization_id(payment) or next((authorization_id(i) for i in instructions if authorization_id(i)), "") or authorization_id(subscription)
        authorization_source = "payment" if authorization_id(payment) else "instruction" if any(authorization_id(i) for i in instructions) else "subscription" if authorization_id(subscription) else "none"
        remote_linked = bool(aid)
        ref = str(payment.get("externalReference") or subscription.get("externalReference") or "")
        token = ref.split(":", 1)[1] if ref.startswith(("co:", "checkout:", "checkout_upgrade:")) else ""
        session = sessions_by_payment.get(pid) or sessions_by_token.get(token) or sessions_by_auth.get(aid) or {}
        local_sub = local_by_remote.get(sid) or local_by_user.get(session.get("user_id")) or {}
        if not session and local_sub:
            local_reference = str(local_sub.get("external_reference") or "")
            local_token = local_reference.split(":", 1)[1] if local_reference.startswith(("checkout:", "checkout_upgrade:", "co:")) else ""
            session = sessions_by_token.get(local_token) or latest_by_user.get(local_sub.get("user_id"), {})
        metadata = session.get("metadata", {})
        aid = aid or metadata.get("asaas_pix_automatic_authorization_id", "")
        if aid and authorization_source == "none":
            authorization_source = "checkout"
        method, state = payment_method(payment.get("billingType")), str(payment.get("status") or "UNKNOWN").upper()
        overdue = state in OPEN and due < today
        findings = []
        pix = pix_info(aid, method, metadata, instructions, remote_linked)
        candidates = [a for a in auths_by_customer.get(resource_id(payment.get("customer")), []) if a["id"] != aid] if method == "PIX" else []
        if candidates and not aid:
            # Same customer is not proof of linkage to this particular contract or charge.
            pix["pix_kind"] = "unverified"
            pix["authorization_status"] = "UNKNOWN"
            findings.append("Cliente possui autorização Pix, mas o vínculo com esta cobrança não foi confirmado")
        elif any(a["status"] == "ACTIVE" for a in candidates):
            findings.append("Cliente possui outra autorização ativa; confira se substitui a autorização deste registro")
        if method == "PIX":
            if pix["authorization_status"] != "ACTIVE":
                findings.append("Autorização Pix ausente, inativa ou não verificada")
            if not remote_linked:
                findings.append("Cobrança sem vínculo confirmado com Pix Automático")
            if pix["creation_mode"] == "MANUAL":
                findings.append("Próximos ciclos dependem da aplicação")
            if any(i.get("status") == "REFUSED" for i in instructions):
                findings.append("Instrução de débito recusada")
            if pix["local_authorization_status"] and pix["authorization_status"] not in {pix["local_authorization_status"], "UNKNOWN"}:
                findings.append("Autorização diverge do cadastro local")
        if overdue and local_sub.get("status") == "active":
            findings.append("Cobrança vencida com assinatura local ativa")
        if not local_sub:
            findings.append("Sem assinatura local vinculada")
        rows.append({
            "id": f"payment:{pid}", "kind": "payment", "scope": "subscription" if sid or aid or local_sub else "unmatched",
            "subscription_key": sid or aid or (f"local:{local_sub['id']}" if local_sub else pid),
            "local_subscription_id": local_sub.get("id"), "user_id": local_sub.get("user_id"),
            "name": local_sub.get("name") or session.get("name") or resource_id(payment.get("customer")) or "Sem identificação",
            "email": local_sub.get("email") or session.get("email") or "", "plan": local_sub.get("plan") or session.get("plan") or "—",
            "gateway": "asaas", "method": method, "local_method": local_sub.get("method"),
            "local_status": local_sub.get("status"), "remote_status": subscription.get("status"),
            "payment_id": pid, "remote_subscription_id": sid or None, "customer_id": resource_id(payment.get("customer")),
            "external_reference": ref, "due_date": due.isoformat(), "days_overdue": (today - due).days if overdue else 0,
            "amount": money(payment.get("value")), "net_amount": money(payment.get("netValue")),
            "payment_status": state, "paid_date": payment.get("paymentDate") or payment.get("clientPaymentDate"),
            "classification": "overdue" if overdue else "paid" if state in PAID else "other",
            "evidence": "asaas", "invoice_url": payment.get("invoiceUrl"), "findings": findings,
            "customer_authorizations": candidates, "authorization_source": authorization_source, **pix,
        })

    rows_by_local, rows_by_remote = {}, {}
    for row in rows:
        if row["local_subscription_id"]:
            rows_by_local.setdefault(row["local_subscription_id"], []).append(row)
        if row["remote_subscription_id"]:
            rows_by_remote.setdefault(row["remote_subscription_id"], []).append(row)
    audits, represented_remote = [], set()
    for sub in local:
        sid = (sub.get("asaas_subscription_id") or "") if sub["provider"] == "asaas" else ""
        if sid:
            represented_remote.add(sid)
        session = latest_by_user.get(sub["user_id"], {}) if sub["provider"] == "asaas" else {}
        reference = str(sub.get("external_reference") or "")
        if sub["provider"] == "asaas" and reference.startswith(("checkout:", "checkout_upgrade:", "co:")):
            session = sessions_by_token.get(reference.split(":", 1)[1]) or session
        metadata, remote_sub = session.get("metadata", {}), subs.get(sid, {})
        aid = authorization_id(remote_sub) or metadata.get("asaas_pix_automatic_authorization_id", "")
        expected = as_date(metadata.get("asaas_pix_automatic_next_due_date")) or as_date(remote_sub.get("nextDueDate"))
        if not expected and as_date(sub.get("valid_until")):
            expected = as_date(sub["valid_until"]) + timedelta(days=1)
        related = rows_by_local.get(sub["id"], [])
        pix = pix_info(aid, payment_method(sub.get("method")), metadata, [], bool(authorization_id(remote_sub)))
        if sub["provider"] != "asaas" and pix["pix_kind"] != "not_pix":
            pix.update(pix_kind="unknown", authorization_status="UNKNOWN", creation_mode="UNKNOWN")
        audits.append({"id": sub["id"], "name": sub["name"], "email": sub["email"], "gateway": sub["provider"],
                       "plan": sub["plan"], "status": sub["status"], "remote_status": remote_sub.get("status"),
                       "remote_subscription_id": sid or None, "method": payment_method(sub.get("method")),
                       "expected_date": expected.isoformat() if expected else None,
                       "overdue_count": sum(r["classification"] == "overdue" for r in related), **pix})
        if not expected or expected >= today or expected > end or (start and expected < start):
            continue
        if sub["status"] in {"cancelled", "canceled", "refunded", "cancel_at_period_end"} or str(remote_sub.get("status") or "").upper() in {"INACTIVE", "EXPIRED"}:
            continue
        if any(as_date(r["due_date"]) >= expected and r["payment_status"] in PAID | OPEN for r in related):
            continue
        reason = "Gateway não consultado: conferir renovação" if sub["provider"] != "asaas" else "Renovação esperada sem cobrança correspondente no período consultado"
        rows.append({"id": f"local:{sub['id']}", "kind": "expectation", "scope": "subscription",
                     "subscription_key": f"local:{sub['id']}", "local_subscription_id": sub["id"], "user_id": sub["user_id"],
                     "name": sub["name"], "email": sub["email"], "plan": sub["plan"], "gateway": sub["provider"],
                     "method": payment_method(sub.get("method")), "local_method": sub.get("method"),
                     "local_status": sub["status"], "remote_status": remote_sub.get("status"), "payment_id": None,
                     "remote_subscription_id": sid or None, "customer_id": sub.get("asaas_customer_id"), "external_reference": None,
                     "due_date": expected.isoformat(), "days_overdue": (today - expected).days, "amount": None, "net_amount": None,
                     "payment_status": "UNVERIFIED", "paid_date": None, "classification": "review", "evidence": "local",
                     "invoice_url": None, "findings": [reason], **pix})
    for sid, sub in subs.items():
        due = as_date(sub.get("nextDueDate"))
        if sid in represented_remote or not due or not (due < today and due <= end) or (start and due < start) or sub.get("status") != "ACTIVE":
            continue
        if any(as_date(r["due_date"]) >= due for r in rows_by_remote.get(sid, [])):
            continue
        aid = authorization_id(sub)
        rows.append({"id": f"remote:{sid}", "kind": "expectation", "scope": "subscription", "subscription_key": sid,
                     "local_subscription_id": None, "user_id": None, "name": resource_id(sub.get("customer")), "email": "", "plan": "—",
                     "gateway": "asaas", "method": payment_method(sub.get("billingType")), "local_method": None,
                     "local_status": None, "remote_status": sub.get("status"), "payment_id": None,
                     "remote_subscription_id": sid, "customer_id": resource_id(sub.get("customer")), "external_reference": sub.get("externalReference"),
                     "due_date": due.isoformat(), "days_overdue": (today - due).days, "amount": None, "net_amount": None,
                     "payment_status": "UNVERIFIED", "paid_date": None, "classification": "review", "evidence": "asaas_subscription",
                     "invoice_url": None, "findings": ["Assinatura remota sem cadastro local e com próxima cobrança vencida"],
                     **pix_info(aid, payment_method(sub.get("billingType")), {}, [], bool(aid))})
    return {"rows": sorted(rows, key=lambda r: (r["classification"] != "overdue", -r["days_overdue"], r["id"])),
            "subscriptions": audits,
            "authorization_inventory": {
                "total": len(auths), "complete": remote["authorizations"]["complete"],
                "by_status": {status: sum(str(a.get("status") or "UNKNOWN").upper() == status for a in auths.values())
                              for status in {"ACTIVE", "CREATED", "REFUSED", "CANCELLED", "EXPIRED", "UNKNOWN"}},
            },
            "coverage": {name: {"complete": value["complete"], "count": len(value["data"]), "error": value["error"]}
                         for name, value in remote.items()},
            "complete": all(value["complete"] for value in remote.values()),
            "generated_at": datetime.now(timezone.utc).isoformat(), "as_of": today.isoformat(),
            "start_date": start.isoformat() if start else None, "end_date": end.isoformat(), "timezone": "America/Sao_Paulo"}


def load_local(db) -> tuple[list[dict], list[dict]]:
    from app.models.subscription import Subscription
    from app.models.checkout import CheckoutSession
    from app.models.user import User
    local = [{"id": s.id, "user_id": u.id, "name": u.name, "email": u.email, "plan": s.plan,
              "provider": str(s.provider or "unknown").lower(), "status": str(s.status or "").lower(),
              "method": s.payment_method_type, "valid_until": s.valid_until, "external_reference": s.external_reference,
              "asaas_subscription_id": s.asaas_subscription_id, "asaas_customer_id": s.asaas_customer_id}
             for s, u in db.query(Subscription, User).join(User, User.id == Subscription.user_id).all()]
    sessions = [{"token": s.token, "user_id": s.user_id, "name": s.customer_name, "email": s.customer_email, "status": s.status,
                 "plan": s.plan_key, "asaas_payment_id": s.asaas_payment_id,
                 "metadata": s.metadata_json if isinstance(s.metadata_json, dict) else {}}
                for s in db.query(CheckoutSession).order_by(CheckoutSession.created_at.desc(), CheckoutSession.id.desc()).all()]
    return local, sessions


def sao_paulo_today() -> date:
    return datetime.now(ZoneInfo("America/Sao_Paulo")).date()
