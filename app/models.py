from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    # Map this model to the users table.
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Require an email and prevent duplicate emails at the database level.
    email: Mapped[str] = mapped_column(
        String(254),
        unique=True,
        nullable=False,
    )

    # Store the password hash, never the original password.
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # PostgreSQL supplies the creation timestamp when inserting a user.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class JobApplication(Base):
    __tablename__ = "job_applications"

    # Enforce allowed statuses in the database as well as in API validation.
    __table_args__ = (
        CheckConstraint(
            "status IN ('saved', 'applied', 'interviewing', 'offer', 'rejected')",
            name="ck_job_applications_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # Link each application to an existing user; the index helps ownership queries.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    company: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    job_title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="saved",
    )

    # Optional fields allow NULL when no value is provided.
    job_url: Mapped[str | None] = mapped_column(Text)

    notes: Mapped[str | None] = mapped_column(Text)

    applied_on: Mapped[date | None] = mapped_column(Date)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # SQLAlchemy sets updated_at when it emits an UPDATE without an explicit value.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )