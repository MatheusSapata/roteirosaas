from __future__ import annotations

import ipaddress
import logging
import re
import secrets
import string
from dataclasses import dataclass
from typing import Optional

import dns.exception
import dns.resolver
from publicsuffix2 import get_sld

from app.core.config import Settings, get_settings


DNS_ALLOWED_CHARS = set(string.ascii_lowercase + string.digits + "-.")


@dataclass
class DnsRecordInstruction:
    type: str
    host: str
    value: str
    fqdn: str
    description: Optional[str] = None


@dataclass
class DomainDnsInstructions:
    is_apex: bool
    txt_record: DnsRecordInstruction
    target_record: DnsRecordInstruction


@dataclass
class DomainVerificationResult:
    success: bool
    txt_verified: bool
    target_verified: bool
    txt_error: Optional[str] = None
    target_error: Optional[str] = None
    observed_target: Optional[str] = None


logger = logging.getLogger(__name__)


class DomainVerificationService:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._resolver = dns.resolver.Resolver()
        self._blocked_hosts = self._load_blocked_hosts()

    def _load_blocked_hosts(self) -> set[str]:
        blocked_hosts: set[str] = set()
        for host in self.settings.forbidden_custom_hosts:
            if not host:
                continue
            try:
                blocked_hosts.add(self.normalize_input_host(host))
            except ValueError:
                logger.warning("Ignorando forbidden_custom_host invalido: %s", host)
        return blocked_hosts

    @staticmethod
    def normalize_input_host(raw: str) -> str:
        if not raw:
            raise ValueError("Informe um host.")
        value = raw.strip()
        if not value:
            raise ValueError("Informe um host.")
        value = re.sub(r"^https?://", "", value, flags=re.IGNORECASE)
        value = value.split("/", 1)[0]
        value = value.split("?", 1)[0]
        value = value.split("#", 1)[0]
        if ":" in value:
            value = value.split(":", 1)[0]
        value = value.rstrip(".").lower()
        if not value or "." not in value:
            raise ValueError("Informe um dominio completo (ex: minhaagencia.com).")
        if any(char not in DNS_ALLOWED_CHARS for char in value):
            raise ValueError("O host informado possui caracteres invalidos.")
        if value.startswith("-") or value.endswith("-"):
            raise ValueError("O host informado nao pode iniciar ou terminar com '-'.")
        try:
            ipaddress.ip_address(value)
            raise ValueError("Informe um host de dominio, nao um IP direto.")
        except ValueError:
            pass
        return value

    @staticmethod
    def generate_token() -> str:
        return "ro_verify_" + secrets.token_hex(6)

    def ensure_allowed_host(self, host: str) -> str:
        normalized = self.normalize_input_host(host)
        if normalized in self._blocked_hosts:
            raise ValueError("O host informado faz parte da infraestrutra da plataforma.")
        return normalized

    def _split_host(self, host: str) -> tuple[bool, str, Optional[str]]:
        base = get_sld(host) or host
        if host == base:
            return True, base, None
        if host.endswith("." + base):
            sub = host[: -len(base) - 1]
            return False, base, sub
        return True, host, None

    def build_instructions(self, host: str, token: str) -> DomainDnsInstructions:
        normalized = self.normalize_input_host(host)
        is_apex, base_domain, sub = self._split_host(normalized)
        txt_host = self.settings.domain_verification_prefix
        if not is_apex and sub:
            txt_host = f"{txt_host}.{sub}"
        txt_fqdn = f"{txt_host}.{base_domain}"

        target_type = "A" if is_apex else "CNAME"
        target_host = "@" if is_apex else (sub or "")
        if is_apex and not self.settings.custom_domain_apex_ip:
            raise ValueError("CUSTOM_DOMAIN_APEX_IP nao configurado para dominios raiz.")
        target_value = self.settings.custom_domain_apex_ip if is_apex else self.settings.custom_domain_cname_target
        txt_record = DnsRecordInstruction(type="TXT", host=txt_host, value=token, fqdn=txt_fqdn)
        description = "Use @ para o dominio raiz" if is_apex else f"Use apenas '{target_host}' como host/subdominio."
        target_record = DnsRecordInstruction(
            type=target_type,
            host=target_host or "@",
            value=target_value or "",
            fqdn=normalized,
            description=description,
        )
        return DomainDnsInstructions(is_apex=is_apex, txt_record=txt_record, target_record=target_record)

    def verify(self, host: str, token: str) -> DomainVerificationResult:
        instructions = self.build_instructions(host, token)
        txt_ok = False
        target_ok = False
        txt_error: Optional[str] = None
        target_error: Optional[str] = None
        observed_target: Optional[str] = None

        try:
            answers = self._resolver.resolve(instructions.txt_record.fqdn, "TXT", raise_on_no_answer=False)
            for answer in answers:
                for value in answer.strings:
                    decoded = value.decode("utf-8")
                    if token in decoded:
                        txt_ok = True
                        break
                if txt_ok:
                    break
            if not txt_ok:
                txt_error = (
                    f"Nao encontramos o registro TXT {instructions.txt_record.fqdn} ou ele nao contem o token esperado."
                )
        except dns.exception.DNSException as exc:
            txt_error = f"Nao foi possivel consultar o registro TXT: {exc}"

        record_type = instructions.target_record.type
        expected_value = instructions.target_record.value
        try:
            answers = self._resolver.resolve(instructions.target_record.fqdn, record_type, raise_on_no_answer=False)
            values: list[str] = []
            for answer in answers:
                if record_type == "CNAME":
                    target = answer.target.to_text().rstrip(".").lower()
                    values.append(target)
                else:
                    target = answer.address
                    values.append(target)
            if not values:
                target_error = f"Nao encontramos o registro {record_type} para {instructions.target_record.fqdn}."
            else:
                observed_target = ", ".join(values)
                normalized_expected = (expected_value or "").strip().lower()
                normalized_values = {value.strip().lower() for value in values}
                if normalized_expected and normalized_expected in normalized_values:
                    target_ok = True
                else:
                    target_error = (
                        f"O {record_type} atual aponta para {observed_target}, mas esperamos {expected_value}."
                    )
        except dns.exception.DNSException as exc:
            target_error = f"Nao foi possivel consultar o registro {record_type}: {exc}"

        success = txt_ok and target_ok
        return DomainVerificationResult(
            success=success,
            txt_verified=txt_ok,
            target_verified=target_ok,
            txt_error=txt_error,
            target_error=target_error,
            observed_target=observed_target,
        )
