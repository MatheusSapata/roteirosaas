from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional
from uuid import uuid4

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobClient, BlobServiceClient, ContentSettings

from app.core.config import get_settings
from app.services.image_optimizer import variant_name

logger = logging.getLogger(__name__)

IMMUTABLE_CACHE = "public, max-age=31536000, immutable"


@dataclass
class StoredFile:
    name: str
    size: int
    last_modified: datetime | None
    tier: str  # Hot, Cool, Cold, Archive (local: Hot)
    rehydrating: bool = False


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

    def blob_name_from_url(self, url: str) -> Optional[str]:
        """Nome do arquivo quando o endereço é do nosso armazenamento no Azure (senão, None)."""
        if not self.is_remote or not self._base_url:
            return None
        prefix = f"{self._base_url}/"
        if not url.startswith(prefix):
            return None
        name = url[len(prefix):].split("?", 1)[0].split("#", 1)[0]
        return name if name and "/" not in name else None

    def public_url(self, blob_name: str) -> str:
        assert self._base_url
        return f"{self._base_url}/{blob_name}"

    def exists(self, blob_name: str) -> bool:
        return self.is_remote and self._build_blob_client(blob_name).exists()

    def read_bytes(self, blob_name: str) -> bytes:
        return self._build_blob_client(blob_name).download_blob().readall()

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

    # --- Ciclo de vida dos arquivos (arquivamento e limpeza) ---

    def list_files(self) -> Iterator[StoredFile]:
        """Todos os arquivos guardados, com tamanho, data e camada do Azure."""
        if self.is_remote:
            assert self._blob_service and self._container_name
            container = self._blob_service.get_container_client(self._container_name)
            for blob in container.list_blobs():
                tier = getattr(blob, "blob_tier", None)
                yield StoredFile(
                    name=blob.name,
                    size=int(blob.size or 0),
                    last_modified=blob.last_modified,
                    tier=str(getattr(tier, "value", tier) or "Hot"),
                    rehydrating=bool(getattr(blob, "archive_status", None)),
                )
            return
        if not self._local_dir.exists():
            return
        for path in self._local_dir.iterdir():
            if path.is_file():
                stat = path.stat()
                yield StoredFile(
                    name=path.name,
                    size=stat.st_size,
                    last_modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                    tier="Hot",
                )

    def set_tier(self, name: str, tier: str) -> None:
        """Muda a camada do arquivo no Azure (Hot, Cool, Archive). Sem Azure, não faz nada.
        Sair do Archive leva algumas horas (o Azure "reidrata" o arquivo)."""
        if self.is_remote:
            self._build_blob_client(name).set_standard_blob_tier(tier)

    def delete_file(self, name: str) -> None:
        if self.is_remote:
            self._build_blob_client(name).delete_blob(delete_snapshots="include")
            return
        path = self._local_dir / name
        if path.is_file():
            path.unlink()


media_storage = MediaStorage()