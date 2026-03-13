from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: Literal["dev", "prod", "test"] = Field("dev", alias="ENV")
    database_url: str = Field(..., alias="DATABASE_URL")
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(720, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_minutes: int = Field(43200, alias="REFRESH_TOKEN_EXPIRE_MINUTES")
    app_name: str = Field("Travel Pages SaaS", alias="APP_NAME")
    mp_access_token: str | None = Field(None, alias="MP_ACCESS_TOKEN")
    mp_webhook_url: str | None = Field(None, alias="MP_WEBHOOK_URL")
    mp_success_url: str | None = Field(None, alias="MP_SUCCESS_URL")
    mp_failure_url: str | None = Field(None, alias="MP_FAILURE_URL")
    mp_payer_test_email: str | None = Field(None, alias="MP_PAYER_TEST_EMAIL")
    stripe_secret_key: str | None = Field(None, alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str | None = Field(None, alias="STRIPE_WEBHOOK_SECRET")
    stripe_price_essencial: str | None = Field(None, alias="STRIPE_PRICE_ESSENCIAL")
    stripe_price_growth: str | None = Field(None, alias="STRIPE_PRICE_GROWTH")
    stripe_price_infinity: str | None = Field(None, alias="STRIPE_PRICE_INFINITY")
    stripe_success_url: str | None = Field(None, alias="STRIPE_SUCCESS_URL")
    stripe_cancel_url: str | None = Field(None, alias="STRIPE_CANCEL_URL")
    asaas_api_key: str | None = Field(None, alias="ASAAS_API_KEY")
    asaas_base_url: str = Field("https://sandbox.asaas.com/api/v3", alias="ASAAS_BASE_URL")
    asaas_billing_type: Literal["BOLETO", "CREDIT_CARD", "PIX"] = Field(
        "CREDIT_CARD", alias="ASAAS_BILLING_TYPE"
    )
    asaas_success_url: str | None = Field(None, alias="ASAAS_SUCCESS_URL")
    password_reset_token_minutes: int = Field(60, alias="PASSWORD_RESET_TOKEN_MINUTES")
    azure_storage_connection_string: str | None = Field(None, alias="AZURE_STORAGE_CONNECTION_STRING")
    azure_storage_container: str | None = Field(None, alias="AZURE_STORAGE_CONTAINER")
    azure_storage_base_url: str | None = Field(None, alias="AZURE_STORAGE_BASE_URL")
    viajechat_api_base_url: str = Field("https://painel.viajechat.com.br/api/v1", alias="VIAJECHAT_API_BASE_URL")
    viajechat_api_key: str | None = Field(None, alias="VIAJECHAT_API_KEY")
    viajechat_tag_trial_5days: str | None = Field(None, alias="VIAJECHAT_TAG_TRIAL_5DAYS")
    viajechat_tag_trial_3days: str | None = Field(None, alias="VIAJECHAT_TAG_TRIAL_3DAYS")
    viajechat_tag_trial_1day: str | None = Field(None, alias="VIAJECHAT_TAG_TRIAL_1DAY")
    viajechat_tag_trial_overdue: str | None = Field(None, alias="VIAJECHAT_TAG_TRIAL_OVERDUE_1DAY")
    trial_tag_job_hour: int = Field(8, alias="TRIAL_TAG_JOB_HOUR")
    trial_tag_job_minute: int = Field(0, alias="TRIAL_TAG_JOB_MINUTE")
    trial_tag_job_timezone: str = Field("America/Sao_Paulo", alias="TRIAL_TAG_JOB_TIMEZONE")
    cakto_webhook_secret: str | None = Field(None, alias="CAKTO_WEBHOOK_SECRET")
    cakto_password_token_minutes: int = Field(240, alias="CAKTO_PASSWORD_TOKEN_MINUTES")
    cakto_offer_essencial_monthly: str | None = Field(None, alias="CAKTO_OFFER_ESSENCIAL_MONTHLY")
    cakto_offer_essencial_annual: str | None = Field(None, alias="CAKTO_OFFER_ESSENCIAL_ANNUAL")
    cakto_offer_growth_monthly: str | None = Field(None, alias="CAKTO_OFFER_GROWTH_MONTHLY")
    cakto_offer_growth_annual: str | None = Field(None, alias="CAKTO_OFFER_GROWTH_ANNUAL")
    cakto_offer_infinity_monthly: str | None = Field(None, alias="CAKTO_OFFER_INFINITY_MONTHLY")
    cakto_offer_infinity_annual: str | None = Field(None, alias="CAKTO_OFFER_INFINITY_ANNUAL")
    cakto_offer_teste_monthly: str | None = Field(None, alias="CAKTO_OFFER_TESTE_MONTHLY")
    cakto_offer_teste_annual: str | None = Field(None, alias="CAKTO_OFFER_TESTE_ANNUAL")
    cakto_product_essencial_monthly: str | None = Field(None, alias="CAKTO_PRODUCT_ESSENCIAL_MONTHLY")
    cakto_product_essencial_annual: str | None = Field(None, alias="CAKTO_PRODUCT_ESSENCIAL_ANNUAL")
    cakto_product_growth_monthly: str | None = Field(None, alias="CAKTO_PRODUCT_GROWTH_MONTHLY")
    cakto_product_growth_annual: str | None = Field(None, alias="CAKTO_PRODUCT_GROWTH_ANNUAL")
    cakto_product_infinity_monthly: str | None = Field(None, alias="CAKTO_PRODUCT_INFINITY_MONTHLY")
    cakto_product_infinity_annual: str | None = Field(None, alias="CAKTO_PRODUCT_INFINITY_ANNUAL")
    cakto_product_teste_monthly: str | None = Field(None, alias="CAKTO_PRODUCT_TESTE_MONTHLY")
    cakto_product_teste_annual: str | None = Field(None, alias="CAKTO_PRODUCT_TESTE_ANNUAL")
    cakto_api_base_url: str | None = Field(None, alias="CAKTO_API_BASE_URL")
    cakto_client_id: str | None = Field(None, alias="CAKTO_CLIENT_ID")
    cakto_client_secret: str | None = Field(None, alias="CAKTO_CLIENT_SECRET")
    platform_domains: list[str] = Field(
        default_factory=lambda: ["roteiroonline.com", "www.roteiroonline.com", "localhost"],
        alias="PLATFORM_DOMAINS",
    )
    forbidden_custom_hosts: list[str] = Field(
        default_factory=lambda: ["roteiroonline.com", "www.roteiroonline.com", "localhost"],
        alias="FORBIDDEN_CUSTOM_HOSTS",
    )
    custom_domain_cname_target: str = Field("roteiroonline.com", alias="CUSTOM_DOMAIN_CNAME_TARGET")
    custom_domain_apex_ip: str | None = Field(None, alias="CUSTOM_DOMAIN_APEX_IP")
    domain_verification_prefix: str = Field("_roteiroonline-verification", alias="DOMAIN_VERIFICATION_PREFIX")
    platform_primary_domain: str | None = Field(None, alias="PLATFORM_PRIMARY_DOMAIN")
    custom_domain_ssl_provider: str | None = Field(None, alias="CUSTOM_DOMAIN_SSL_PROVIDER")

    @field_validator("platform_domains", "forbidden_custom_hosts", mode="before")
    @classmethod
    def split_csv_list(cls, value):
        if not value:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def normalized_platform_domains(self) -> list[str]:
        return [host.strip().lower() for host in self.platform_domains if host.strip()]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, populate_by_name=True, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
