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
    sale,
    sale_item,
    product,
    schedule,
    rooming,
    stripe_account,
    legal,
    transport,
)  # noqa: E402,F401
