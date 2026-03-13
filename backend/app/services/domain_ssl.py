from __future__ import annotations

from typing import Optional

from app.core.config import Settings, get_settings
from app.models.agency_domain import AgencyDomain


class DomainSslService:
    """Camada de integracao futura com emissao de SSL (ex.: Certbot, Cloudflare)."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.provider_name = self.settings.custom_domain_ssl_provider

    def queue_certificate_request(self, domain: AgencyDomain) -> None:
        """
        Dispara (ou simula) um pedido de emissao de certificado.

        Atualmente mantemos um stub interno que apenas ajusta o status para
        'requested' quando existe um provider configurado ou 'pending' caso
        a emissao seja manual.
        """

        if self.provider_name:
            domain.ssl_status = "requested"
            domain.ssl_last_error = None
        else:
            domain.ssl_status = "pending"
            domain.ssl_last_error = "SSL provider nao configurado; emissao manual necessaria."

    def can_activate(self, domain: AgencyDomain) -> bool:
        """
        Indica se as condicoes minimas para ativar o dominio foram atendidas.

        Sem provider configurado, consideramos a verificacao DNS suficiente.
        Caso exista provider, exigimos o status 'issued'.
        """

        if not domain.is_verified:
            return False
        if not self.provider_name:
            return True
        return domain.ssl_status in {"issued"}
