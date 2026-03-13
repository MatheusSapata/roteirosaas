from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Optional

from app.core.config import Settings, get_settings
from app.models.agency_domain import AgencyDomain


class DomainSslService:
    """Camada de integracao futura com emissao de SSL (ex.: Certbot, Cloudflare)."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.logger = logging.getLogger(__name__)
        provider = (self.settings.custom_domain_ssl_provider or "").strip()
        if provider.lower() == "manual":
            provider = ""
        self.provider_name = provider or None
        self.script_path = self.settings.custom_domain_ssl_script_path

    def queue_certificate_request(self, domain: AgencyDomain) -> None:
        """
        Dispara (ou simula) um pedido de emissao de certificado.

        Atualmente mantemos um stub interno que apenas ajusta o status para
        'requested' quando existe um provider configurado ou 'pending' caso
        a emissao seja manual.
        """

        if self.provider_name == "certbot" and self.script_path:
            script = Path(self.script_path)
            if not script.exists():
                domain.ssl_status = "error"
                domain.ssl_last_error = f"Script de SSL nao encontrado em {script}."
                self.logger.error("Script SSL inexistente: %s", script)
                return
            if not script.is_file():
                domain.ssl_status = "error"
                domain.ssl_last_error = f"O caminho {script} nao e um arquivo executavel."
                self.logger.error("Script SSL invalido: %s", script)
                return
            try:
                domain.ssl_status = "requested"
                domain.ssl_last_error = None
                subprocess.check_call(
                    [str(script), domain.host],
                    timeout=300,
                )
                domain.ssl_status = "issued"
                domain.ssl_last_error = None
            except subprocess.CalledProcessError as exc:
                domain.ssl_status = "error"
                domain.ssl_last_error = f"Falha ao emitir certificado: {exc}"
                self.logger.exception("Erro executando script SSL para %s", domain.host)
            except subprocess.TimeoutExpired:
                domain.ssl_status = "error"
                domain.ssl_last_error = "Certbot demorou demais para responder."
                self.logger.error("Timeout emitindo SSL para %s", domain.host)
        elif self.provider_name:
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
