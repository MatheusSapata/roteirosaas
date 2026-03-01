from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: Literal["dev", "prod", "test"] = Field("dev", alias="ENV")
    database_url: str = Field(..., alias="DATABASE_URL")
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(720, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
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
    password_reset_token_minutes: int = Field(60, alias="PASSWORD_RESET_TOKEN_MINUTES")
    azure_storage_connection_string: str | None = Field(None, alias="AZURE_STORAGE_CONNECTION_STRING")
    azure_storage_container: str | None = Field(None, alias="AZURE_STORAGE_CONTAINER")
    azure_storage_base_url: str | None = Field(None, alias="AZURE_STORAGE_BASE_URL")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, populate_by_name=True, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
