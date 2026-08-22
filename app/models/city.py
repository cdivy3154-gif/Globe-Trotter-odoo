import uuid
from datetime import datetime, UTC
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Enum as SQLEnum, ForeignKey, Float, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ActivityType(str, PyEnum):
    SIGHTSEEING = "sightseeing"
    FOOD = "food"
    ADVENTURE = "adventure"
    CULTURE = "culture"
    NATURE = "nature"
    NIGHTLIFE = "nightlife"
    SHOPPING = "shopping"
    RELAXATION = "relaxation"


class ActivitySource(str, PyEnum):
    SEED = "seed"
    CUSTOM = "custom"
    EXTERNAL = "external"


class City(Base):
    __tablename__ = "cities"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    timezone: Mapped[str] = mapped_column(String(100), default="UTC", nullable=False)
    cost_index: Mapped[int] = mapped_column(Integer, default=50, nullable=False)  # 1-100
    popularity_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    stops: Mapped[list["Stop"]] = relationship("Stop", back_populates="city", lazy="selectin")
    activities_catalog: Mapped[list["ActivityCatalog"]] = relationship(
        "ActivityCatalog", back_populates="city", cascade="all, delete-orphan", lazy="selectin"
    )
    saved_by_users: Mapped[list["UserSavedDestination"]] = relationship(
        "UserSavedDestination", back_populates="city", cascade="all, delete-orphan", lazy="selectin"
    )


class ActivityCatalog(Base):
    __tablename__ = "activities_catalog"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    city_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    activity_type: Mapped[ActivityType] = mapped_column(
        SQLEnum(ActivityType), nullable=False, index=True
    )
    avg_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[ActivitySource] = mapped_column(
        SQLEnum(ActivitySource), default=ActivitySource.SEED, nullable=False
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    city: Mapped["City"] = relationship("City", back_populates="activities_catalog", lazy="selectin")