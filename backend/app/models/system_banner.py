from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class SystemBanner(Base):
    __tablename__ = "system_banners"

    id = Column(Integer, primary_key=True, index=True)
    internal_name = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    subtitle = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")
    priority = Column(Integer, nullable=False, server_default="0")

    has_icon = Column(Boolean, nullable=False, server_default="true")
    icon_name = Column(String(100), nullable=True)
    background_variant = Column(String(50), nullable=False, server_default="green_gradient")
    dismissible = Column(Boolean, nullable=False, server_default="true")
    dismiss_behavior = Column(String(30), nullable=False, server_default="hide_forever")
    dismiss_duration_days = Column(Integer, nullable=True)

    has_cta = Column(Boolean, nullable=False, server_default="true")
    cta_label = Column(String(100), nullable=True)
    cta_type = Column(String(30), nullable=True)
    cta_target = Column(Text, nullable=True)

    placement = Column(String(50), nullable=False, server_default="dashboard", index=True)
    rules_match_mode = Column(String(10), nullable=False, server_default="all")
    target_plans = Column(JSONB, nullable=True)
    target_subscription_statuses = Column(JSONB, nullable=True)
    target_agency_ids = Column(JSONB, nullable=True)
    target_user_roles = Column(JSONB, nullable=True)
    starts_at = Column(DateTime(timezone=True), nullable=True, index=True)
    ends_at = Column(DateTime(timezone=True), nullable=True, index=True)
    max_views_per_user = Column(Integer, nullable=True)
    max_views_per_agency = Column(Integer, nullable=True)
    hide_after_click = Column(Boolean, nullable=False, server_default="false")
    rule_config = Column(JSONB, nullable=True)

    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    events = relationship("BannerEvent", back_populates="banner", cascade="all, delete-orphan", passive_deletes=True)
    dismissals = relationship(
        "BannerDismissal", back_populates="banner", cascade="all, delete-orphan", passive_deletes=True
    )


class BannerEvent(Base):
    __tablename__ = "banner_events"

    id = Column(Integer, primary_key=True, index=True)
    banner_id = Column(Integer, ForeignKey("system_banners.id", ondelete="CASCADE"), nullable=False, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(30), nullable=False, index=True)
    event_metadata = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    banner = relationship("SystemBanner", back_populates="events")


class BannerDismissal(Base):
    __tablename__ = "banner_dismissals"

    id = Column(Integer, primary_key=True, index=True)
    banner_id = Column(Integer, ForeignKey("system_banners.id", ondelete="CASCADE"), nullable=False, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    dismissed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    permanent = Column(Boolean, nullable=False, server_default="false")

    banner = relationship("SystemBanner", back_populates="dismissals")
