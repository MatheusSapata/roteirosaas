import re
from typing import Annotated, Any, Literal, Optional

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

TAG_PRESET_COLORS = ("blue", "amber", "rose", "violet", "teal", "orange", "slate", "green")
_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def _check_tag_color(value: str) -> str:
    """Cor da tag: uma das cores prontas ou uma cor personalizada em #RRGGBB (guardada em minúsculas)."""
    value = (value or "").strip()
    if value in TAG_PRESET_COLORS:
        return value
    if _HEX_COLOR.match(value):
        return value.lower()
    raise ValueError("Cor inválida. Use uma das cores prontas ou uma cor no formato #RRGGBB.")


TagColor = Annotated[str, AfterValidator(_check_tag_color)]


class PageTagBrief(BaseModel):
    id: int
    name: str
    color: str
    model_config = ConfigDict(from_attributes=True)


class TagSectionUse(BaseModel):
    page_id: int
    page_title: str


class PageTagOut(PageTagBrief):
    page_count: int = 0
    sections: list[TagSectionUse] = []


class PageTagCreate(BaseModel):
    agency_id: int
    name: str = Field(min_length=1, max_length=60)
    color: Optional[TagColor] = None


class PageTagUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=60)
    color: Optional[TagColor] = None


class PageTagMerge(BaseModel):
    into_tag_id: int


class PageTagsSet(BaseModel):
    tag_ids: list[int]


class PageTagsBulk(BaseModel):
    agency_id: int
    page_ids: list[int] = Field(min_length=1)
    add_tag_ids: list[int] = []
    remove_tag_ids: list[int] = []


class TagCardsRequest(BaseModel):
    """Regra da seção Links/Roteiros por tag, para a prévia no editor."""

    section: dict[str, Any]


class TagCardExcluded(BaseModel):
    pageId: int
    title: str
    reason: Literal["current", "draft", "past", "limit"]


class TagCardsOut(BaseModel):
    items: list[dict[str, Any]]
    excluded: list[TagCardExcluded]
