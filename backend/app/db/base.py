from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import models here for Alembic autogenerate
from app.models import (
    user,
    agency,
    page_template,
    page,
    media,
    stats,
    agency_user,
    subscription,
    pixel,
    lesson,
    cakto,
    agency_domain,
    revenue,
    lead_form,
    user_session,
    external_api_key,
    flight_lookup_cache,
    flight_section,
)  # noqa: E402,F401
