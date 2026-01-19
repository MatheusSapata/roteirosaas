from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_superuser, get_db
from app.models.page_template import PageTemplate
from app.schemas.page_template import PageTemplateCreate, PageTemplateOut, PageTemplateUpdate
from app.models.user import User

router = APIRouter()


@router.get("", response_model=list[PageTemplateOut])
def list_templates(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> list[PageTemplateOut]:
    return db.query(PageTemplate).all()


@router.get("/{template_id}", response_model=PageTemplateOut)
def get_template(
    template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
) -> PageTemplateOut:
    template = db.query(PageTemplate).filter(PageTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("", response_model=PageTemplateOut, dependencies=[Depends(get_current_superuser)])
def create_template(template_in: PageTemplateCreate, db: Session = Depends(get_db)) -> PageTemplateOut:
    existing = db.query(PageTemplate).filter(PageTemplate.slug == template_in.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Template slug already exists")
    template = PageTemplate(**template_in.dict())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.put("/{template_id}", response_model=PageTemplateOut, dependencies=[Depends(get_current_superuser)])
def update_template(template_id: int, template_in: PageTemplateUpdate, db: Session = Depends(get_db)) -> PageTemplateOut:
    template = db.query(PageTemplate).filter(PageTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    for key, value in template_in.dict(exclude_unset=True).items():
        setattr(template, key, value)
    db.add(template)
    db.commit()
    db.refresh(template)
    return template
