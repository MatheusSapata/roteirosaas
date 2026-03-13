from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.agency_domain import AgencyDomain
from app.models.agency import Agency


@dataclass
class PublicPageResolution:
    agency_slug: str
    page_slug: Optional[str]
    mode: Literal["platform_path", "custom_domain"]
    host: str
    normalized_host: str
    scheme: str
    path: str


class PublicPageResolverService:
    RESERVED_PATH_PREFIXES = ("/api", "/assets", "/uploads", "/static", "/admin")
    RESERVED_EXACT_PATHS = {"/favicon.ico", "/robots.txt"}

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.platform_hosts = {
            normalized for host in self.settings.platform_domains if (normalized := self._normalize_hostname(host))
        }

    @staticmethod
    def _normalize_hostname(value: str | None) -> str | None:
        if not value:
            return None
        trimmed = value.strip().lower()
        if not trimmed:
            return None
        if ":" in trimmed:
            trimmed = trimmed.split(":", 1)[0]
        return trimmed

    @staticmethod
    def _extract_page_slug(path: str) -> Optional[str]:
        cleaned = path.strip("/")
        if not cleaned:
            return None
        parts = [part for part in cleaned.split("/") if part]
        if not parts:
            return None
        if len(parts) > 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pagina nao encontrada.")
        return parts[0]

    def _resolve_custom_domain(
        self,
        normalized_host: str,
        raw_host: str,
        path: str,
        scheme: str,
        db: Session,
    ) -> PublicPageResolution:
        if any(path.startswith(prefix) for prefix in self.RESERVED_PATH_PREFIXES):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurso nao disponivel.")
        if path in self.RESERVED_EXACT_PATHS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurso nao disponivel.")

        domain: AgencyDomain | None = (
            db.query(AgencyDomain)
            .join(Agency, Agency.id == AgencyDomain.agency_id)
            .filter(
                func.lower(AgencyDomain.host) == normalized_host,
                AgencyDomain.is_active.is_(True),
                AgencyDomain.is_verified.is_(True),
            )
            .first()
        )
        if not domain or not domain.agency:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dominio nao configurado.")

        page_slug = self._extract_page_slug(path)
        return PublicPageResolution(
            agency_slug=domain.agency.slug,
            page_slug=page_slug,
            mode="custom_domain",
            host=raw_host,
            normalized_host=normalized_host,
            scheme=scheme,
            path=path,
        )

    def resolve(
        self,
        host_header: str | None,
        path: str,
        scheme: str,
        agency_slug_param: Optional[str],
        page_slug_param: Optional[str],
        db: Session,
    ) -> PublicPageResolution:
        normalized_host = self._normalize_hostname(host_header)
        host_value = host_header or ""

        if normalized_host in self.platform_hosts or not normalized_host:
            if agency_slug_param is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agencia nao encontrada.")
            return PublicPageResolution(
                agency_slug=agency_slug_param,
                page_slug=page_slug_param,
                mode="platform_path",
                host=host_value,
                normalized_host=normalized_host or "",
                scheme=scheme,
                path=path,
            )

        return self._resolve_custom_domain(normalized_host, host_value, path, scheme, db)
