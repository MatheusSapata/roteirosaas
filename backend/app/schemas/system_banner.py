from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


PlacementType = Literal["dashboard", "global", "pages", "leads", "clients", "opportunities", "settings"]
CtaType = Literal["internal_route", "external_url", "none"]
DismissBehavior = Literal["hide_forever", "hide_for_days", "show_again_next_session", "never_hide"]
RulesMatchMode = Literal["all", "any"]


class SystemBannerBase(BaseModel):
    internal_name: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=255)
    subtitle: str | None = None
    is_active: bool = True
    priority: int = 0

    has_icon: bool = True
    icon_name: str | None = "TrendingUp"
    background_variant: str = "green_gradient"
    dismissible: bool = True
    dismiss_behavior: DismissBehavior = "hide_forever"
    dismiss_duration_days: int | None = None

    has_cta: bool = True
    cta_label: str | None = "Conectar Pixel"
    cta_type: CtaType | None = "internal_route"
    cta_target: str | None = "/admin/integracoes"

    placement: PlacementType = "dashboard"
    rules_match_mode: RulesMatchMode = "all"
    target_plans: list[str] | None = None
    target_subscription_statuses: list[str] | None = None
    target_agency_ids: list[int] | None = None
    target_user_roles: list[str] | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    max_views_per_user: int | None = None
    max_views_per_agency: int | None = None
    hide_after_click: bool = False
    rule_config: dict[str, Any] | None = None


class SystemBannerCreate(SystemBannerBase):
    pass


class SystemBannerUpdate(BaseModel):
    internal_name: str | None = Field(default=None, min_length=1, max_length=255)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    subtitle: str | None = None
    is_active: bool | None = None
    priority: int | None = None
    has_icon: bool | None = None
    icon_name: str | None = None
    background_variant: str | None = None
    dismissible: bool | None = None
    dismiss_behavior: DismissBehavior | None = None
    dismiss_duration_days: int | None = None
    has_cta: bool | None = None
    cta_label: str | None = None
    cta_type: CtaType | None = None
    cta_target: str | None = None
    placement: PlacementType | None = None
    rules_match_mode: RulesMatchMode | None = None
    target_plans: list[str] | None = None
    target_subscription_statuses: list[str] | None = None
    target_agency_ids: list[int] | None = None
    target_user_roles: list[str] | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    max_views_per_user: int | None = None
    max_views_per_agency: int | None = None
    hide_after_click: bool | None = None
    rule_config: dict[str, Any] | None = None


class SystemBannerOut(SystemBannerBase):
    id: int
    created_by_user_id: int | None = None
    updated_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SystemBannerListItem(SystemBannerOut):
    impressions: int = 0
    clicks: int = 0
    dismissals: int = 0
    ctr: float = 0.0


class SystemBannerListResponse(BaseModel):
    items: list[SystemBannerListItem]
    total: int


class EligibleBannerResponse(BaseModel):
    banner: SystemBannerOut | None = None


class BannerEventIn(BaseModel):
    agency_id: int | None = None
    metadata: dict[str, Any] | None = None


class BannerDismissIn(BaseModel):
    agency_id: int | None = None
    mode: DismissBehavior | None = None
    dismiss_duration_days: int | None = None


class BannerStatsOut(BaseModel):
    banner_id: int
    impressions: int
    clicks: int
    dismissals: int
    ctr: float


class BannerEligibilityContextIn(BaseModel):
    placement: PlacementType = "dashboard"
    plan: str | None = None
    subscription_status: str | None = None
    agency_id: int | None = None
    role: str | None = None


class BannerEligibilityTestIn(SystemBannerBase):
    context: BannerEligibilityContextIn = Field(default_factory=BannerEligibilityContextIn)


class BannerEligibilityTestOut(BaseModel):
    eligible: bool
    reasons: list[str] = Field(default_factory=list)
