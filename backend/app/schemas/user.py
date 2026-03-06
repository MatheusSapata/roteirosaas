from typing import Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, field_validator


class UserBase(BaseModel):
    email: EmailStr
    name: str
    plan: str = "free"
    subscription_id: Optional[int] = None
    cpf: Optional[str] = None
    cnpj: Optional[str] = None
    whatsapp: Optional[str] = None
    address_street: Optional[str] = None
    address_number: Optional[str] = None
    address_complement: Optional[str] = None
    address_neighborhood: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zipcode: Optional[str] = None


class UtmData(BaseModel):
    source: Optional[str] = None
    medium: Optional[str] = None
    campaign: Optional[str] = None
    term: Optional[str] = None
    content: Optional[str] = None
    referrer: Optional[str] = None


class UserCreate(UserBase):
    password: str
    cpf: str
    whatsapp: str
    utm: Optional[UtmData] = None

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, value: str) -> str:
        digits = "".join(filter(str.isdigit, value or ""))
        if not digits or len(digits) != 11:
            raise ValueError("CPF inválido")

        # Validação dos dígitos verificadores
        def check_digit(nums: list[int]) -> int:
            s = sum(v * i for v, i in zip(nums, range(len(nums) + 1, 1, -1)))
            d = 11 - (s % 11)
            return d if d < 10 else 0

        numbers = [int(d) for d in digits]
        if len(set(numbers)) == 1:
            raise ValueError("CPF inválido")
        if check_digit(numbers[:9]) != numbers[9] or check_digit(numbers[:10]) != numbers[10]:
            raise ValueError("CPF inválido")

        return digits

    @field_validator("whatsapp")
    @classmethod
    def sanitize_whatsapp(cls, value: str) -> str:
        sanitized = "".join(filter(str.isdigit, value or ""))
        if not sanitized:
            raise ValueError("Informe o WhatsApp")
        return sanitized

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        digits = "".join(filter(str.isdigit, value))
        if digits and len(digits) != 14:
            raise ValueError("CNPJ invǭlido")
        return digits or None

    @field_validator("address_zipcode")
    @classmethod
    def sanitize_zipcode(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        digits = "".join(filter(str.isdigit, value))
        if digits and len(digits) != 8:
            raise ValueError("CEP invǭlido")
        return digits or None

    @field_validator("address_state")
    @classmethod
    def sanitize_state(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = value.strip().upper()
        if normalized and len(normalized) != 2:
            raise ValueError("UF invǭlida")
        return normalized or None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    plan: Optional[str] = None
    subscription_id: Optional[int] = None
    cpf: Optional[str] = None
    cnpj: Optional[str] = None
    whatsapp: Optional[str] = None
    address_street: Optional[str] = None
    address_number: Optional[str] = None
    address_complement: Optional[str] = None
    address_neighborhood: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zipcode: Optional[str] = None

    @field_validator("whatsapp")
    @classmethod
    def sanitize_whatsapp(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        sanitized = "".join(filter(str.isdigit, value))
        return sanitized or None

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        digits = "".join(filter(str.isdigit, value))
        if digits and len(digits) != 14:
            raise ValueError("CNPJ invǭlido")
        return digits or None

    @field_validator("address_zipcode")
    @classmethod
    def sanitize_zipcode(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        digits = "".join(filter(str.isdigit, value))
        if digits and len(digits) != 8:
            raise ValueError("CEP invǭlido")
        return digits or None

    @field_validator("address_state")
    @classmethod
    def sanitize_state(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = value.strip().upper()
        if normalized and len(normalized) != 2:
            raise ValueError("UF invǭlida")
        return normalized or None


class UserOut(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    trial_plan: Optional[str] = None
    trial_original_plan: Optional[str] = None
    trial_started_at: Optional[datetime] = None
    trial_ends_at: Optional[datetime] = None
    trial_ack_start: Optional[bool] = None
    trial_ack_end: Optional[bool] = None
    trial_warn_3days_ack: Optional[bool] = None
    trial_warn_1day_ack: Optional[bool] = None
    trial_blocked: Optional[bool] = None
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    password: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class PasswordResetByProfile(BaseModel):
    email: EmailStr
    cpf: str
    password: str

    @field_validator("cpf")
    @classmethod
    def normalize_cpf(cls, value: str) -> str:
        digits = "".join(filter(str.isdigit, value or ""))
        if len(digits) != 11:
            raise ValueError("CPF invalido")
        return digits
