from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import models here for Alembic autogenerate
from app.models import user, agency, page_template, page, media, stats, agency_user, subscription, pixel  # noqa: E402,F401
