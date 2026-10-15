from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


CheckoutThemeMode = Literal["light", "dark"]
# Modelo do checkout: "classic" (imagem na coluna lateral) ou "banner" (banner no topo, mobile first,
# inspirado no checkout do Viaje On).
CheckoutLayout = Literal["classic", "banner"]
CheckoutPaymentMethod = Literal["pix", "card"]
CheckoutDiscountType = Literal["fixed", "percent"]


class CheckoutAppearanceIn(BaseModel):
    key: str = Field(..., min_length=1, max_length=120)
    name: str = Field(..., min_length=1, max_length=255)
    theme_mode: CheckoutThemeMode = "dark"
    layout: CheckoutLayout = "classic"
    desktop_image_url: str | None = None
    mobile_banner_url: str | None = None
    active: bool = True

    @field_validator("key")
    @classmethod
    def normalize_key(cls, value: str) -> str:
        return value.strip().lower()


class CheckoutAppearanceOut(CheckoutAppearanceIn):
    pass


class CheckoutPixelIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    pixel_id: str = Field(..., min_length=1, max_length=120)
    access_token: str = Field(..., min_length=1, max_length=500)
    active: bool = True
    offer_keys: list[str] = Field(default_factory=list)

    @field_validator("name", "pixel_id", "access_token")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("offer_keys")
    @classmethod
    def normalize_offer_keys(cls, values: list[str]) -> list[str]:
        return [value.strip().lower() for value in values if value and value.strip()]


class CheckoutPixelOut(CheckoutPixelIn):
    pass


class CheckoutPixelPublicOut(BaseModel):
    name: str
    pixel_id: str
    active: bool = True


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
    # Plano único da página de vendas e da tela de planos: a oferta que aparece como a
    # assinatura mensal ou a anual. Uma oferta por ciclo, com o mesmo ciclo de cobrança.
    sales_slot: Literal["monthly", "annual"] | None = None
    # Parcelas no cartão (só no anual; 1 = só à vista). As parcelas seguem a tabela de repasse
    # das taxas do Asaas (app/services/card_installments.py); um valor fixo por número de
    # parcelas (ex.: {"12": 97.00}) vale no lugar da conta.
    max_installments: int = Field(default=1, ge=1, le=12)
    installment_fixed_values: dict[str, Decimal] = Field(default_factory=dict)
    # Promoção da 1ª mensalidade (só no mensal e só para quem assina pela primeira vez):
    # a 1ª cobrança sai por first_payment_amount até first_payment_ends_at; depois, o valor cheio.
    first_payment_amount: Decimal | None = Field(default=None, gt=0)
    first_payment_ends_at: datetime | None = None

    @field_validator("key")
    @classmethod
    def normalize_key(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("sales_slot", mode="before")
    @classmethod
    def normalize_sales_slot(cls, value: Any) -> Any:
        normalized = str(value or "").strip().lower()
        return normalized or None

    @field_validator("checkout_key")
    @classmethod
    def normalize_checkout_key(cls, value: str | None) -> str | None:
        normalized = (value or "").strip().lower()
        return normalized or None

    @field_validator("installment_fixed_values", mode="before")
    @classmethod
    def normalize_installment_fixed_values(cls, value: Any) -> Any:
        from app.services.card_installments import normalize_fixed_values

        if not isinstance(value, dict):
            return {}
        return {str(count): amount for count, amount in normalize_fixed_values(value).items()}

    @field_validator("first_payment_amount", mode="before")
    @classmethod
    def normalize_first_payment_amount(cls, value: Any) -> Any:
        return None if value in (None, "") else value

    @field_validator("first_payment_ends_at", mode="before")
    @classmethod
    def normalize_first_payment_ends_at(cls, value: Any) -> Any:
        if value in (None, ""):
            return None
        return value

    @field_validator("first_payment_ends_at")
    @classmethod
    def ends_at_with_timezone(cls, value: datetime | None) -> datetime | None:
        # Sem fuso, a data vem da tela do admin no horário de Brasília.
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=ZoneInfo("America/Sao_Paulo"))
        return value

    @model_validator(mode="after")
    def keep_rules_per_cycle(self) -> "CheckoutOfferIn":
        # Parcelas só no anual; promoção da 1ª mensalidade só no mensal.
        if self.billing_cycle == "monthly":
            self.max_installments = 1
            self.installment_fixed_values = {}
        else:
            self.first_payment_amount = None
            self.first_payment_ends_at = None
        self.installment_fixed_values = {
            count: amount for count, amount in self.installment_fixed_values.items() if int(count) <= self.max_installments
        }
        return self


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
    pixels: list[CheckoutPixelIn] = Field(default_factory=list)


class CheckoutSettingsOut(BaseModel):
    id: int
    is_active: bool
    offers: list[CheckoutOfferOut] = Field(default_factory=list)
    coupons: list[CheckoutCouponOut] = Field(default_factory=list)
    checkouts: list[CheckoutAppearanceOut] = Field(default_factory=list)
    pixels: list[CheckoutPixelOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CheckoutSalesPlanOfferOut(BaseModel):
    key: str
    title: str
    billing_cycle: Literal["monthly", "annual"]
    amount: Decimal
    # Maior parcelamento no cartão (ex.: 12x de R$ 97,00); 1 = só à vista.
    max_installments: int = 1
    installment_value: Decimal | None = None
    # Promoção da 1ª mensalidade em vigor (None quando não há ou já acabou).
    first_payment_amount: Decimal | None = None
    first_payment_ends_at: datetime | None = None


class CheckoutSalesPlanOut(BaseModel):
    """Plano único à venda: a oferta mensal e a anual (None quando não há)."""

    monthly: CheckoutSalesPlanOfferOut | None = None
    annual: CheckoutSalesPlanOfferOut | None = None


class CheckoutPublicConfigOut(BaseModel):
    theme_mode: CheckoutThemeMode
    layout: CheckoutLayout = "classic"
    desktop_image_url: str | None = None
    mobile_banner_url: str | None = None
    offer: CheckoutOfferOut
    pixels: list[CheckoutPixelPublicOut] = Field(default_factory=list)


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
    # Renovação de plano antigo pelo valor que o cliente pagava (sem cupom e sem promoção).
    is_legacy_renewal: bool = False
    locked_profile_fields: dict[str, bool] | None = None
    # Valor da 1ª cobrança quando a promoção da 1ª mensalidade vale para esta compra.
    first_payment_amount: Decimal | None = None
    # Parcelas do cartão para esta compra (1x à vista sempre primeiro).
    installment_options: list["CheckoutInstallmentOptionOut"] = Field(default_factory=list)


class CheckoutInstallmentOptionOut(BaseModel):
    count: int
    value: Decimal
    total: Decimal
    no_interest: bool = False


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


CheckoutSessionOut.model_rebuild()
