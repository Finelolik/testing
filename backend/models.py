from pydantic import BaseModel, EmailStr, field_validator
import re


class AppealCreate(BaseModel):
    full_name: str
    phone: str
    email: str
    subject: str
    body: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        pattern = r"^\+7 \(\d{3}\) \d{3} \d{2}-\d{2}$"
        if not re.match(pattern, v):
            raise ValueError("Телефон должен быть в формате +7 (xxx) xxx xx-xx")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if len(v.split()) < 2:
            raise ValueError("Укажите имя и фамилию")
        return v

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Тема слишком короткая")
        return v

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 20:
            raise ValueError("Текст обращения слишком короткий")
        return v


class AppealResponse(BaseModel):
    id: int
    full_name: str
    phone: str
    email: str
    subject: str
    body: str
    status: str
    created_at: str


class AdminLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
