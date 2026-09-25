import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import pages
from app.models.agency import Agency
from app.schemas.page import PageCreate, PagePublish, PageUpdate


@pytest.mark.parametrize("plan,limit", [("free", 1), ("trial", 3), ("essencial", 3), ("growth", 10)])
def test_only_published_pages_count_toward_limit(db_session, monkeypatch, plan, limit):
    monkeypatch.setattr(pages, "ensure_agency_member", lambda *args: None)
    monkeypatch.setattr(pages, "ensure_pages_editor_permission", lambda *args: None)
    monkeypatch.setattr(pages, "resolve_agency_plan", lambda *args: plan)
    agency = Agency(name="Limits", slug="limits")
    db_session.add(agency)
    db_session.commit()

    def create(index, status="draft"):
        return pages.create_page(
            PageCreate(agency_id=agency.id, title=f"Page {index}", slug=f"page-{index}",
                       status=status, config_json={"sections": []}),
            current_user=None, db=db_session,
        )

    drafts = [create(index) for index in range(limit + 2)]
    for page in drafts[:limit]:
        pages.publish_page(page.id, PagePublish(), current_user=None, db=db_session)

    extra = create("extra")
    assert extra.status == "draft"
    for action in (
        lambda: pages.publish_page(extra.id, PagePublish(), current_user=None, db=db_session),
        lambda: create("direct", status="published"),
        lambda: pages.update_page(extra.id, PageUpdate(status="published"), current_user=None, db=db_session),
    ):
        with pytest.raises(HTTPException) as error:
            action()
        assert error.value.status_code == 403
        assert error.value.headers["X-Plan-Max-Pages"] == str(limit)

    pages.update_page(drafts[0].id, PageUpdate(title="Updated", status="published"), current_user=None, db=db_session)
    pages.publish_page(drafts[0].id, PagePublish(publish=False), current_user=None, db=db_session)
    pages.publish_page(extra.id, PagePublish(), current_user=None, db=db_session)
    assert extra.status == "published"
