from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator


# Validate registration input, including email format and password length.
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)

    # Normalize the email before Pydantic validates it.
    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if isinstance(value, str):
            return value.strip().lower()
        return value


class UserRead(BaseModel):
    # Allow creating this response schema from a SQLAlchemy model's attributes.
    model_config = ConfigDict(from_attributes=True)

    # Only these fields are returned; the password hash is excluded.
    id: int
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str


# Restrict status values to these five strings.
ApplicationStatus = Literal[
    "saved",
    "applied",
    "interviewing",
    "offer",
    "rejected",
]


class ApplicationCreate(BaseModel):
    # Reject unexpected fields instead of silently ignoring them.
    model_config = ConfigDict(extra="forbid")

    company: str = Field(min_length=1, max_length=100)
    job_title: str = Field(min_length=1, max_length=150)
    status: ApplicationStatus = "saved"
    job_url: HttpUrl | None = None
    notes: str | None = Field(default=None, max_length=2000)
    applied_on: date | None = None

    # Trim first so whitespace-only values fail the minimum-length check.
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


class ApplicationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Fields can be omitted for PATCH; the endpoint updates only submitted fields.
    company: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    job_title: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    status: ApplicationStatus | None = None
    job_url: HttpUrl | None = None
    notes: str | None = Field(default=None, max_length=2000)
    applied_on: date | None = None

    @field_validator("company", "job_title", mode="before")
    @classmethod
    def trim_text(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    # These fields may be omitted, but cannot be explicitly set to null.
    # Optional fields such as notes and applied_on can be cleared with null.
    @field_validator("company", "job_title", "status")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("This field cannot be null.")
        return value


# Return the current page alongside the total matching count and pagination values.
class ApplicationList(BaseModel):
    items: list[ApplicationRead]
    total: int
    limit: int
    offset: int