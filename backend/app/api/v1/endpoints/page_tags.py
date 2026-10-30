from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_active_user, get_db
from app.api.v1.endpoints.pages import ensure_agency_member, ensure_pages_editor_permission
from app.models.page import Page
from app.models.page_tag import PageTag, page_tag_links
from app.models.user import User
from app.schemas.page_tag import (
    PageTagBrief,
    PageTagCreate,
    PageTagMerge,
    PageTagOut,
    PageTagsBulk,
    PageTagsSet,
    PageTagUpdate,
    TagCardsOut,
    TagCardsRequest,
    TagSectionUse,
)
from app.services.page_tags import (
    TAG_COLORS,
    clean_tag_name,
    replace_tag_in_sections,
    resolve_tag_section,
    sections_using_tags,
    slugify_tag,
)

router = APIRouter()


def _get_tag(db: Session, tag_id: int, user: User, *, edit: bool = True) -> PageTag:
    tag = db.query(PageTag).filter(PageTag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada.")
    ensure_agency_member(db, tag.agency_id, user)
    if edit:
        ensure_pages_editor_permission(db, tag.agency_id, user)
    return tag


def _tags_out(db: Session, agency_id: int, tags: list[PageTag]) -> list[PageTagOut]:
    counts = dict(
        db.query(page_tag_links.c.tag_id, func.count(page_tag_links.c.page_id))
        .filter(page_tag_links.c.tag_id.in_([tag.id for tag in tags] or [0]))
        .group_by(page_tag_links.c.tag_id)
        .all()
    )
    usage = sections_using_tags(db, agency_id)
    return [
        PageTagOut(
            id=tag.id,
            name=tag.name,
            color=tag.color,
            page_count=counts.get(tag.id, 0),
            sections=[TagSectionUse(**use) for use in usage.get(tag.id, [])],
        )
        for tag in tags
    ]


def _ensure_unique_name(db: Session, agency_id: int, slug: str, tag_id: int | None = None) -> None:
    query = db.query(PageTag).filter(PageTag.agency_id == agency_id, PageTag.slug == slug)
    if tag_id:
        query = query.filter(PageTag.id != tag_id)
    clash = query.first()
    if clash:
        raise HTTPException(status_code=409, detail=f'Já existe a tag "{clash.name}". Use "Juntar com outra tag" para unir as duas.')


def tags_of_agency(db: Session, agency_id: int, tag_ids: list[int]) -> list[PageTag]:
    """Tags pedidas que pertencem à agência. Id de outra agência dá erro."""
    ids = list(dict.fromkeys(tag_ids))
    if not ids:
        return []
    tags = db.query(PageTag).filter(PageTag.agency_id == agency_id, PageTag.id.in_(ids)).all()
    if len(tags) != len(ids):
        raise HTTPException(status_code=400, detail="Alguma tag não existe nesta agência.")
    return tags


@router.get("", response_model=list[PageTagOut])
def list_tags(
    agency_id: int = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[PageTagOut]:
    ensure_agency_member(db, agency_id, current_user)
    tags = db.query(PageTag).filter(PageTag.agency_id == agency_id).order_by(func.lower(PageTag.name)).all()
    return _tags_out(db, agency_id, tags)


@router.post("", response_model=PageTagOut)
def create_tag(
    payload: PageTagCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PageTagOut:
    ensure_agency_member(db, payload.agency_id, current_user)
    ensure_pages_editor_permission(db, payload.agency_id, current_user)
    name = clean_tag_name(payload.name)
    slug = slugify_tag(name)
    if not slug:
        raise HTTPException(status_code=422, detail="Use letras ou números no nome da tag.")
    # Criar uma tag que já existe devolve a existente: no editor, digitar "europa" escolhe "Europa".
    existing = db.query(PageTag).filter(PageTag.agency_id == payload.agency_id, PageTag.slug == slug).first()
    if existing:
        return _tags_out(db, payload.agency_id, [existing])[0]
    color = payload.color
    if not color:
        used = {row[0] for row in db.query(PageTag.color).filter(PageTag.agency_id == payload.agency_id).all()}
        count = db.query(PageTag).filter(PageTag.agency_id == payload.agency_id).count()
        color = next((c for c in TAG_COLORS if c not in used), TAG_COLORS[count % len(TAG_COLORS)])
    tag = PageTag(agency_id=payload.agency_id, name=name, slug=slug, color=color)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return _tags_out(db, payload.agency_id, [tag])[0]


@router.put("/{tag_id}", response_model=PageTagOut)
def update_tag(
    tag_id: int,
    payload: PageTagUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PageTagOut:
    tag = _get_tag(db, tag_id, current_user)
    if payload.name is not None:
        name = clean_tag_name(payload.name)
        slug = slugify_tag(name)
        if not slug:
            raise HTTPException(status_code=422, detail="Use letras ou números no nome da tag.")
        _ensure_unique_name(db, tag.agency_id, slug, tag.id)
        tag.name, tag.slug = name, slug
    if payload.color is not None:
        tag.color = payload.color
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return _tags_out(db, tag.agency_id, [tag])[0]


@router.delete("/{tag_id}")
def delete_tag(
    tag_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    tag = _get_tag(db, tag_id, current_user)
    replace_tag_in_sections(db, tag.agency_id, tag.id, None)
    tag.pages = []
    db.delete(tag)
    db.commit()
    return JSONResponse({"detail": "Tag apagada."})


@router.post("/{tag_id}/merge", response_model=PageTagOut)
def merge_tag(
    tag_id: int,
    payload: PageTagMerge,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PageTagOut:
    """Junta a tag em outra: as páginas e as seções passam para a tag que fica e esta deixa de existir."""
    source = _get_tag(db, tag_id, current_user)
    if payload.into_tag_id == source.id:
        raise HTTPException(status_code=400, detail="Escolha outra tag para juntar.")
    target = db.query(PageTag).filter(PageTag.id == payload.into_tag_id, PageTag.agency_id == source.agency_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="A tag escolhida não existe nesta agência.")
    for page in list(source.pages):
        if target not in page.tags:
            page.tags.append(target)
    replace_tag_in_sections(db, source.agency_id, source.id, target.id)
    source.pages = []
    db.delete(source)
    db.commit()
    db.refresh(target)
    return _tags_out(db, target.agency_id, [target])[0]


@router.post("/bulk", response_model=list[PageTagOut])
def bulk_tags(
    payload: PageTagsBulk,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[PageTagOut]:
    """Coloca e/ou tira tags de várias páginas de uma vez (seleção na lista de páginas)."""
    ensure_agency_member(db, payload.agency_id, current_user)
    ensure_pages_editor_permission(db, payload.agency_id, current_user)
    add = tags_of_agency(db, payload.agency_id, payload.add_tag_ids)
    remove_ids = {tag.id for tag in tags_of_agency(db, payload.agency_id, payload.remove_tag_ids)}
    pages = (
        db.query(Page)
        .options(selectinload(Page.tags))
        .filter(Page.agency_id == payload.agency_id, Page.id.in_(payload.page_ids))
        .all()
    )
    if len(pages) != len(set(payload.page_ids)):
        raise HTTPException(status_code=400, detail="Alguma página não existe nesta agência.")
    for page in pages:
        page.tags = [tag for tag in page.tags if tag.id not in remove_ids]
        for tag in add:
            if tag not in page.tags:
                page.tags.append(tag)
    db.commit()
    tags = db.query(PageTag).filter(PageTag.agency_id == payload.agency_id).order_by(func.lower(PageTag.name)).all()
    return _tags_out(db, payload.agency_id, tags)


# Rotas que ficam em /pages/{page_id}/... (tags de uma página e prévia da seção por tag).
pages_router = APIRouter()


def _get_page(db: Session, page_id: int, user: User) -> Page:
    page = db.query(Page).options(selectinload(Page.tags)).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Página não encontrada.")
    ensure_agency_member(db, page.agency_id, user)
    return page


@pages_router.put("/{page_id}/tags", response_model=list[PageTagBrief])
def set_page_tags(
    page_id: int,
    payload: PageTagsSet,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[PageTagBrief]:
    page = _get_page(db, page_id, current_user)
    ensure_pages_editor_permission(db, page.agency_id, current_user)
    page.tags = tags_of_agency(db, page.agency_id, payload.tag_ids)
    db.commit()
    db.refresh(page)
    return [PageTagBrief.model_validate(tag) for tag in page.tags]


@pages_router.post("/{page_id}/tag-cards", response_model=TagCardsOut)
def preview_tag_cards(
    page_id: int,
    payload: TagCardsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TagCardsOut:
    """Cards que a seção Links/Roteiros por tag mostraria agora, com o que ficou de fora e por quê."""
    page = _get_page(db, page_id, current_user)
    items, excluded = resolve_tag_section(db, payload.section, agency=page.agency, host_page_id=page.id)
    return TagCardsOut(items=items, excluded=excluded)
