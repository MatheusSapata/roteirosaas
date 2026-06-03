from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


CheckoutThemeMode = Literal["light", "dark"]
CheckoutPaymentMethod = Literal["pix", "card"]
CheckoutDiscountType = Literal["fixed", "percent"]


class CheckoutAppearanceIn(BaseModel):
    key: str = Field(..., min_length=1, max_length=120)
    name: str = Field(..., min_length=1, max_length=255)
    theme_mode: CheckoutThemeMode = "dark"
    desktop_image_url: str | None = None
    mobile_banner_url: str | None = None
    active: bool = True

    @field_validator("key")
    @classmethod
    def normalize_key(cls, value: str) -> str:
        return value.strip().lower()


class CheckoutAppearanceOut(CheckoutAppearanceIn):
    pass


class CheckoutOfferIn(BaseModel):
    key: str = Field(..., min_length=1, max_length=120)
    title: str = Field(..., min_length=1, max_length=255)
    footer_product_label: str = Field(default="Plano profissional", min_length=1, max_length=120)
    plan_key: str = Field(default="professional", min_length=1, max_length=50)
    billing_cycle: Literal["monthly", "annual"] = "monthly"
    amount: Decimal = Field(default=Decimal("49.90"), gt=0)
    active: bool = True
    subtitle: str | None = None
    checkout_key: str | None = Field(default=None, max_length=120)

    @field_validator("key")
    @classmethod
    def normalize_key(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("checkout_key")
    @classmethod
    def normalize_checkout_key(cls, value: str | None) -> str | None:
        normalized = (value or "").strip().lower()
        return normalized or None


class CheckoutOfferOut(CheckoutOfferIn):
    amount: Decimal


class CheckoutCouponIn(BaseModel):
    code: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=255)
    discount_type: CheckoutDiscountType = "fixed"
    value: Decimal = Field(..., gt=0)
    offer_keys: list[str] = Field(default_factory=list)
    active: bool = True

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("offer_keys")
    @classmethod
    def normalize_offer_keys(cls, values: list[str]) -> list[str]:
        return [value.strip().lower() for value in values if value and value.strip()]


class CheckoutCouponOut(CheckoutCouponIn):
    value: Decimal
    usage_count: int = 0


class CheckoutSettingsUpdate(BaseModel):
    is_active: bool = True
    offers: list[CheckoutOfferIn] = Field(default_factory=list)
    coupons: list[CheckoutCouponIn] = Field(default_factory=list)
    checkouts: list[CheckoutAppearanceIn] = Field(default_factory=list)


class CheckoutSettingsOut(BaseModel):
    id: int
    is_active: bool
    offers: list[CheckoutOfferOut] = Field(default_factory=list)
    coupons: list[CheckoutCouponOut] = Field(default_factory=list)
    checkouts: list[CheckoutAppearanceOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CheckoutPublicConfigOut(BaseModel):
    theme_mode: CheckoutThemeMode
    desktop_image_url: str | None = None
    mobile_banner_url: str | None = None
    offer: CheckoutOfferOut


class CheckoutSessionCreate(BaseModel):
    offer_key: str = Field(..., min_length=1, max_length=120)
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_email: str = Field(..., min_length=3, max_length=255)
    customer_document: str = Field(..., min_length=11, max_length=18)
    customer_phone: str = Field(..., min_length=10, max_length=20)
    customer_zipcode: str = Field(..., min_length=8, max_length=10)
    coupon_code: str | None = Field(default=None, max_length=80)
    metadata: dict[str, Any] | None = None

    @field_validator("offer_key")
    @classmethod
    def normalize_offer_key(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("coupon_code")
    @classmethod
    def normalize_coupon_code(cls, value: str | None) -> str | None:
        normalized = (value or "").strip().upper()
        return normalized or None

    @field_validator("customer_email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("customer_document")
    @classmethod
    def validate_document(cls, value: str) -> str:
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) not in {11, 14}:
            raise ValueError("customer_document must have 11 (CPF) or 14 (CNPJ) digits")
        return value


class CheckoutUpgradeSessionDetailsUpdate(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_email: str = Field(..., min_length=3, max_length=255)
    customer_document: str = Field(..., min_length=11, max_length=18)
    customer_phone: str = Field(..., min_length=10, max_length=20)
    customer_zipcode: str = Field(..., min_length=8, max_length=10)

    @field_validator("customer_document")
    @classmethod
    def validate_document(cls, value: str) -> str:
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) not in {11, 14}:
            raise ValueError("customer_document must have 11 (CPF) or 14 (CNPJ) digits")
        return value


class CheckoutCouponPreviewIn(BaseModel):
    offer_key: str = Field(..., min_length=1, max_length=120)
    coupon_code: str = Field(..., min_length=1, max_length=80)

    @field_validator("offer_key")
    @classmethod
    def normalize_offer_key(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("coupon_code")
    @classmethod
    def normalize_coupon_code(cls, value: str) -> str:
        return value.strip().upper()


class CheckoutCouponPreviewOut(BaseModel):
    offer_key: str
    amount: Decimal
    original_amount: Decimal
    discount_amount: Decimal
    applied_coupon_code: str


class CheckoutSessionOut(BaseModel):
    token: str
    offer_key: str
    product_name: str
    billing_cycle: str
    amount: Decimal
    original_amount: Decimal | None = None
    discount_amount: Decimal | None = None
    applied_coupon_code: str | None = None
    status: str
    payment_method: str | None = None
    pix_mode: Literal["automatic", "conventional"] | None = None
    customer_name: str
    customer_email: str
    customer_document: str
    customer_phone: str
    customer_zipcode: str
    pix_copy_paste: str | None = None
    pix_qr_code_base64: str | None = None
    pix_expiration_date: datetime | None = None
    paid_at: datetime | None = None
    password_defined_at: datetime | None = None
    user_exists: bool = False
    requires_password_setup: bool = True
    is_upgrade: bool = False
    locked_profile_fields: dict[str, bool] | None = None


class CheckoutPixStartRequest(BaseModel):
    token: str


class CheckoutCardStartRequest(BaseModel):
    token: str
    holder_name: str = Field(..., min_length=1, max_length=255)
    card_number: str = Field(..., min_length=13, max_length=24)
    expiry_month: str = Field(..., min_length=2, max_length=2)
    expiry_year: str = Field(..., min_length=2, max_length=4)
    ccv: str = Field(..., min_length=3, max_length=4)
    installment_count: int = Field(default=1, ge=1, le=12)
    remote_ip: str | None = None


class CheckoutPasswordRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=8, max_length=120)


class CheckoutPasswordResponse(BaseModel):
    detail: str
    email: str


class CheckoutTrackEventIn(BaseModel):
    event_name: str = Field(..., min_length=2, max_length=80)
    step: str | None = Field(default=None, max_length=40)
    status: str | None = Field(default=None, max_length=40)
    payment_method: str | None = Field(default=None, max_length=30)
    duration_ms: int | None = Field(default=None, ge=0)
    error_message: str | None = Field(default=None, max_length=2000)
    metadata: dict[str, Any] | None = None


class CheckoutTrackEventOut(BaseModel):
    ok: bool = True


class CheckoutTrackingItemOut(BaseModel):
    id: int
    token: str | None = None
    offer_key: str
    customer_name: str
    customer_email: str
    customer_document: str | None = None
    customer_phone: str
    customer_zipcode: str
    payment_method_selected: str | None = None
    signed_at: datetime | None = None
    password_defined_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    events_count: int = 0
    success_events_count: int = 0
    error_events_count: int = 0
    last_event_name: str | None = None
    last_event_at: datetime | None = None
    last_ip_address: str | None = None
    last_ip_city: str | None = None
    last_ip_region: str | None = None
    last_ip_country: str | None = None
    total_time_seconds: int | None = None
    sessions_count: int = 1


class CheckoutTrackingEventOut(BaseModel):
    id: int
    token: str
    offer_key: str
    event_name: str
    step: str | None = None
    status: str | None = None
    payment_method: str | None = None
    duration_ms: int | None = None
    error_message: str | None = None
    ip_address: str | None = None
    ip_country: str | None = None
    ip_region: str | None = None
    ip_city: str | None = None
    created_at: datetime


class CheckoutTrackingDocumentDetailOut(BaseModel):
    customer_document: str
    customer_name: str
    customer_email: str
    customer_phone: str
    sessions_count: int
    events_count: int
    error_events_count: int
    signed_count: int
    password_defined_count: int
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    events: list[CheckoutTrackingEventOut] = Field(default_factory=list)


class CheckoutOfferReportItemOut(BaseModel):
    offer_key: str
    offer_title: str
    checkout_key: str | None = None
    is_active: bool = True
    signed_count: int = 0
    upgrade_count: int = 0
    direct_count: int = 0
    total_count: int = 0
    last_signed_at: datetime | None = None
