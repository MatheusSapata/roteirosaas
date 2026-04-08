from __future__ import annotations

import base64
import hashlib
from datetime import datetime
from io import BytesIO
from secrets import token_urlsafe

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from app.core.config import get_settings
from app.models.legal import LegalContract, LegalContractSignatureStatus


class LegalVerificationService:
    """Utility responsible for verification metadata, hashes and QR codes."""

    HASH_ALGORITHM = "sha256"

    def __init__(self) -> None:
        self._settings = get_settings()

    def build_verification_url(self, token: str) -> str:
        base = self._settings.resolved_verification_base_url.rstrip("/")
        return f"{base}/verificar/{token}"

    def ensure_contract_metadata(self, contract: LegalContract) -> bool:
        """Ensure token, URL and QR payload exist for signed contracts."""
        if contract.signature_status != LegalContractSignatureStatus.signed.value:
            return False

        changed = False
        if not contract.verification_token:
            contract.verification_token = token_urlsafe(32)
            changed = True

        expected_url = self.build_verification_url(contract.verification_token)
        if contract.verification_url != expected_url:
            contract.verification_url = expected_url
            changed = True

        if contract.verification_url:
            qr_payload = self._build_qr_payload(contract.verification_url)
            if contract.verification_qr_image_data != qr_payload:
                contract.verification_qr_image_data = qr_payload
                changed = True

        return changed

    def attach_pdf_metadata(self, contract: LegalContract, pdf_bytes: bytes) -> None:
        """Persist hash, file size and timestamps derived from the signed PDF."""
        digest = hashlib.sha256(pdf_bytes).hexdigest()
        contract.document_hash = digest
        contract.document_hash_algorithm = self.HASH_ALGORITHM
        contract.signed_pdf_size_bytes = len(pdf_bytes)
        contract.verification_generated_at = datetime.utcnow()

    def serialize_contract(self, contract: LegalContract) -> dict:
        """Return a lightweight dict used by templates and serializers."""
        return {
            "verification_token": contract.verification_token,
            "verification_url": contract.verification_url,
            "verification_qr_image_data": contract.verification_qr_image_data,
            "document_hash": contract.document_hash,
            "document_hash_preview": self._hash_preview(contract.document_hash),
            "document_hash_algorithm": contract.document_hash_algorithm or self.HASH_ALGORITHM,
            "signed_pdf_size_bytes": contract.signed_pdf_size_bytes,
            "verification_generated_at": contract.verification_generated_at,
        }

    def _build_qr_payload(self, url: str) -> str:
        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        image = qr.make_image(fill_color="#0f172a", back_color="white")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    @staticmethod
    def _hash_preview(value: str | None) -> str | None:
        if not value:
            return None
        if len(value) <= 12:
            return value
        return f"{value[:8]}...{value[-6:]}"


legal_verification_service = LegalVerificationService()
