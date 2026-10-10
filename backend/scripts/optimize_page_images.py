"""Gera as versões leves (WebP 640/1280/2400) das imagens que já estão nas páginas.

Imagens enviadas antes da otimização no envio continuam pesadas (vários MB) e aparecem
em faixas no visitante. Este script baixa cada imagem usada nas páginas, cria as versões
leves no mesmo armazenamento e troca o endereço nas páginas (config_json e capa).

Os arquivos originais não são apagados: o mapa antigo → novo fica salvo num JSON, e
basta trocar de volta para desfazer.

Uso (de dentro de backend/):
    python scripts/optimize_page_images.py                  # só simula e mostra a economia
    python scripts/optimize_page_images.py --apply          # grava as versões e atualiza as páginas
    python scripts/optimize_page_images.py --page-id 12 --apply
    python scripts/optimize_page_images.py --agency-id 3 --min-kb 300
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.parse import urlsplit

import httpx
from sqlalchemy.orm.attributes import flag_modified

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal  # noqa: E402
from app.models.page import Page  # noqa: E402
from app.services.image_optimizer import MAIN_WIDTH, optimize_image  # noqa: E402
from app.services.media_storage import media_storage  # noqa: E402

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".jfif", ".png", ".webp", ".bmp", ".tif", ".tiff"}
ALREADY_OPTIMIZED = re.compile(r"_\d+\.webp$", re.IGNORECASE)
LOCAL_UPLOADS = BACKEND_ROOT / "uploads"


def strings_in(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings_in(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings_in(item)


def replace_in(value: Any, mapping: dict[str, str]) -> Any:
    if isinstance(value, str):
        for old, new in mapping.items():
            if old in value:
                value = value.replace(old, new)
        return value
    if isinstance(value, dict):
        return {key: replace_in(item, mapping) for key, item in value.items()}
    if isinstance(value, list):
        return [replace_in(item, mapping) for item in value]
    return value


def media_bases(extra: list[str]) -> list[str]:
    bases = [base.rstrip("/") + "/" for base in extra]
    if media_storage.is_remote and media_storage._base_url:  # noqa: SLF001 - mesmo endereço usado no envio
        bases.append(media_storage._base_url.rstrip("/") + "/")  # noqa: SLF001
    return bases


URL_RE = re.compile(r"""(?:https?://[^\s"'<>()]+|/uploads/[^\s"'<>()]+)""")


def candidate_urls(text: str, bases: list[str]) -> set[str]:
    """Endereços de imagens do nosso armazenamento dentro de um texto (campo ou HTML)."""
    found: set[str] = set()
    for url in URL_RE.findall(text):
        path = urlsplit(url).path
        if "/og-cache/" in path or ALREADY_OPTIMIZED.search(path):
            continue
        if Path(path).suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        if url.startswith("/uploads/") or any(url.startswith(base) for base in bases):
            found.add(url)
    return found


def read_image(url: str, client: httpx.Client) -> Optional[bytes]:
    if url.startswith("/uploads/"):
        path = LOCAL_UPLOADS / url.removeprefix("/uploads/")
        return path.read_bytes() if path.is_file() else None
    response = client.get(url)
    return response.content if response.status_code == 200 else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="grava as versões e atualiza as páginas (sem isso, só simula)")
    parser.add_argument("--page-id", type=int, action="append", default=[], help="só estas páginas (pode repetir)")
    parser.add_argument("--agency-id", type=int, help="só as páginas desta agência")
    parser.add_argument("--min-kb", type=int, default=150, help="ignora imagens menores que isto (padrão 150 KB)")
    parser.add_argument("--base", action="append", default=[], help="outro endereço base de mídia nosso (pode repetir)")
    parser.add_argument("--map-out", help="arquivo JSON com o mapa antigo → novo (padrão: optimize_page_images_<data>.json)")
    args = parser.parse_args()

    bases = media_bases(args.base)
    db = SessionLocal()
    client = httpx.Client(timeout=30, follow_redirects=True)
    try:
        query = db.query(Page)
        if args.page_id:
            query = query.filter(Page.id.in_(args.page_id))
        if args.agency_id:
            query = query.filter(Page.agency_id == args.agency_id)
        pages = query.order_by(Page.id).all()

        urls_by_page: dict[int, set[str]] = {}
        for page in pages:
            texts = list(strings_in(page.config_json or {})) + [page.cover_image_url or ""]
            urls = set().union(*(candidate_urls(text, bases) for text in texts)) if texts else set()
            if urls:
                urls_by_page[page.id] = urls
        unique = sorted(set().union(*urls_by_page.values())) if urls_by_page else []
        print(f"{len(pages)} páginas, {len(urls_by_page)} com imagens, {len(unique)} imagens diferentes.")

        mapping: dict[str, str] = {}
        before_total = after_total = 0
        for url in unique:
            data = read_image(url, client)
            if not data:
                print(f"  não baixou   {url}")
                continue
            if len(data) < args.min_kb * 1024:
                continue
            variants = optimize_image(data)
            if not variants:
                print(f"  sem otimizar {url}")
                continue
            before_total += len(data)
            after_total += len(variants[MAIN_WIDTH])
            print(
                f"  {len(data) // 1024:>6} KB → {len(variants[MAIN_WIDTH]) // 1024:>5} KB "
                f"(celular {len(variants[1280]) // 1024} KB)  {url}"
            )
            if args.apply:
                mapping[url] = media_storage.save_image_variants(variants)

        if before_total:
            print(f"Total: {before_total // 1024} KB → {after_total // 1024} KB na versão maior.")
        if not args.apply:
            print("Simulação: nada foi gravado. Rode com --apply para aplicar.")
            return
        if not mapping:
            print("Nenhuma imagem para trocar.")
            return

        map_path = Path(args.map_out or f"optimize_page_images_{datetime.now():%Y%m%d_%H%M%S}.json")
        map_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Mapa salvo em {map_path} (para desfazer, troque os endereços de volta).")

        changed = 0
        for page in pages:
            page_map = {old: new for old, new in mapping.items() if old in urls_by_page.get(page.id, set())}
            if not page_map:
                continue
            page.config_json = replace_in(page.config_json, page_map)
            flag_modified(page, "config_json")
            if page.cover_image_url:
                page.cover_image_url = replace_in(page.cover_image_url, page_map)
            db.commit()
            changed += 1
        print(f"{changed} páginas atualizadas.")
    finally:
        client.close()
        db.close()


if __name__ == "__main__":
    main()
