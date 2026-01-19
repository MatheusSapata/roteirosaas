from app.models.agency import Agency
from app.models.page import Page


def create_page(db, status: str = "published") -> Page:
    agency = Agency(name="Agencia Teste", slug=f"slug-{status}")
    db.add(agency)
    db.flush()

    page = Page(
        agency_id=agency.id,
        title=f"Page {status}",
        slug=f"page-{status}",
        status=status,
        config_json={"sections": []},
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


def test_stats_only_allow_published_pages(client, db_session):
    published = create_page(db_session, status="published")
    draft = create_page(db_session, status="draft")

    ok = client.post(f"/api/v1/stats/{published.id}/track-visit")
    assert ok.status_code == 200
    assert ok.json()["visits"] == 1

    fail = client.post(f"/api/v1/stats/{draft.id}/track-visit")
    assert fail.status_code == 404
