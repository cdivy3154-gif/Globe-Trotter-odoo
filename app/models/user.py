import uuid
from datetime import datetime, UTC
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class UserRole(str, PyEnum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    language_pref: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), default=UserRole.USER, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    trips: Mapped[list["Trip"]] = relationship(
        "Trip", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    saved_destinations: Mapped[list["UserSavedDestination"]] = relationship(
        "UserSavedDestination", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    copied_trips: Mapped[list["TripCopy"]] = relationship(
        "TripCopy", foreign_keys="TripCopy.copied_by_user_id", back_populates="copied_by_user", lazy="selectin"
    )