import uuid
from datetime import datetime, UTC
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Enum as SQLEnum, ForeignKey, Float, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class TripVisibility(str, PyEnum):
    PRIVATE = "private"
    PUBLIC = "public"


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_photo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    visibility: Mapped[TripVisibility] = mapped_column(
        SQLEnum(TripVisibility), default=TripVisibility.PRIVATE, nullable=False
    )
    share_slug: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    total_budget: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="trips", lazy="selectin")
    stops: Mapped[list["Stop"]] = relationship(
        "Stop", back_populates="trip", cascade="all, delete-orphan", lazy="selectin", order_by="Stop.stop_order"
    )
    share: Mapped["TripShare | None"] = relationship(
        "TripShare", back_populates="trip", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
    copies_from: Mapped[list["TripCopy"]] = relationship(
        "TripCopy", foreign_keys="TripCopy.original_trip_id", back_populates="original_trip", lazy="selectin"
    )
    copies_to: Mapped[list["TripCopy"]] = relationship(
        "TripCopy", foreign_keys="TripCopy.copied_trip_id", back_populates="copied_trip", lazy="selectin"
    )


class Stop(Base):
    __tablename__ = "stops"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    trip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    city_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False
    )
    arrival_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    departure_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    stop_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    trip: Mapped["Trip"] = relationship("Trip", back_populates="stops", lazy="selectin")
    city: Mapped["City"] = relationship("City", back_populates="stops", lazy="selectin")
    activities: Mapped[list["Activity"]] = relationship(
        "Activity", back_populates="stop", cascade="all, delete-orphan", lazy="selectin", order_by="Activity.start_time"
    )