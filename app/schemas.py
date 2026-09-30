from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if isinstance(value, str):
            return value.strip().lower()
        return value


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str

    
    
ApplicationStatus = Literal[
    "saved",
    "applied",
    "interviewing",
    "offer",
    "rejected",
]


class ApplicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: str = Field(min_length=1, max_length=100)
    job_title: str = Field(min_length=1, max_length=150)
    status: ApplicationStatus = "saved"
    job_url: HttpUrl | None = None
    notes: str | None = Field(default=None, max_length=2000)
    applied_on: date | None = None

    @field_validator("company", "job_title", mode="before")
    @classmethod
    def trim_text(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    job_title: str
    status: ApplicationStatus
    job_url: HttpUrl | None
    notes: str | None
    applied_on: date | None
    created_at: datetime
    updated_at: datetime