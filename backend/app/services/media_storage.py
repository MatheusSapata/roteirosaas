from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
from uuid import uuid4

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobClient, BlobServiceClient, ContentSettings

from app.core.config import get_settings
from app.services.image_optimizer import variant_name

logger = logging.getLogger(__name__)

IMMUTABLE_CACHE = "public, max-age=31536000, immutable"


class MediaStorage:
    def __init__(self) -> None:
        settings = get_settings()
        self._local_dir = Path("uploads")
        connection = settings.azure_storage_connection_string
        container = settings.azure_storage_container

        self._blob_service: Optional[BlobServiceClient] = None
        self._container_name: Optional[str] = None
        self._base_url: Optional[str] = None

        if connection and container:
            try:
                self._blob_service = BlobServiceClient.from_connection_string(connection)
                self._container_name = container
                container_client = self._blob_service.get_container_client(container)
                try:
                    container_client.create_container()
                except ResourceExistsError:
                    pass
                account_name = self._blob_service.account_name
                base = settings.azure_storage_base_url or f"https://{account_name}.blob.core.windows.net/{container}"
                self._base_url = base.rstrip("/")
            except Exception as exc:  # pragma: no cover - defensive fallback
                logger.warning("Azure Blob initialization failed, using local media storage: %s", exc)
                self._blob_service = None
                self._container_name = None
                self._base_url = None

    @property
    def is_remote(self) -> bool:
        return self._blob_service is not None and self._container_name is not None

    def _build_blob_client(self, blob_name: str) -> BlobClient:
        assert self._blob_service and self._container_name
        return self._blob_service.get_blob_client(container=self._container_name, blob=blob_name)

    def save(self, data: bytes, filename: str, content_type: Optional[str] = None) -> str:
        extension = Path(filename).suffix or ""
        return self.save_as(data, f"{uuid4()}{extension}", content_type)

    def save_image_variants(self, variants: dict[int, bytes]) -> str:
        """Guarda as larguras de uma imagem otimizada (<id>_<largura>.webp) e devolve a maior."""
        stem = str(uuid4())
        urls = {width: self.save_as(data, variant_name(stem, width), "image/webp") for width, data in variants.items()}
        return urls[max(urls)]

    def save_as(self, data: bytes, blob_name: str, content_type: Optional[str] = None) -> str:
        if self.is_remote:
            blob_client = self._build_blob_client(blob_name)
            # Cada arquivo tem nome único e nunca muda: o navegador pode guardar por um ano.
            content_settings = ContentSettings(content_type=content_type, cache_control=IMMUTABLE_CACHE)
            blob_client.upload_blob(data, overwrite=True, content_settings=content_settings)
            assert self._base_url
            return f"{self._base_url}/{blob_name}"

        self._local_dir.mkdir(exist_ok=True)
        file_path = self._local_dir / blob_name
        with open(file_path, "wb") as buffer:
            buffer.write(data)
        return f"/uploads/{blob_name}"


media_storage = MediaStorage()