from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users" #users database

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(  #email
        String(254),
        unique=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column( #password
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column( #and time created
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
    )