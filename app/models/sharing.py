import uuid
from datetime import datetime, UTC
from sqlalchemy import String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class TripShare(Base):
    __tablename__ = "trip_shares"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    trip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    share_slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    trip: Mapped["Trip"] = relationship("Trip", back_populates="share", lazy="selectin")


class TripCopy(Base):
    __tablename__ = "trip_copies"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    original_trip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    copied_trip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    copied_by_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    original_trip: Mapped["Trip"] = relationship(
        "Trip", foreign_keys=[original_trip_id], back_populates="copies_from", lazy="selectin"
    )
    copied_trip: Mapped["Trip"] = relationship(
        "Trip", foreign_keys=[copied_trip_id], back_populates="copies_to", lazy="selectin"
    )
    copied_by_user: Mapped["User"] = relationship(
        "User", foreign_keys=[copied_by_user_id], back_populates="copied_trips", lazy="selectin"
    )


class UserSavedDestination(Base):
    __tablename__ = "user_saved_destinations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    city_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="saved_destinations", lazy="selectin")
    city: Mapped["City"] = relationship("City", back_populates="saved_by_users", lazy="selectin")