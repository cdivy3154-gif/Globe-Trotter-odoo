import uuid
from datetime import datetime, UTC
from typing import Optional
from sqlalchemy.orm import Session
from app.core.exceptions import NotFoundError, ConflictError, ValidationError
from app.repositories import TripRepository, TripShareRepository, TripCopyRepository, StopRepository, ActivityRepository
from app.models.trip import Trip, Stop, TripVisibility
from app.models.activity import Activity
from app.models.sharing import TripShare, TripCopy
from app.schemas.sharing import TripShareCreate
from app.services.trip_service import TripService


class SharingService:
    def __init__(self, session: Session):
        self.session = session
        self.trip_repo = TripRepository(session)
        self.share_repo = TripShareRepository(session)
        self.copy_repo = TripCopyRepository(session)
        self.stop_repo = StopRepository(session)
        self.activity_repo = ActivityRepository(session)
        self.trip_service = TripService(session)

    def _generate_slug(self) -> str:
        return uuid.uuid4().hex[:12]

    def create_share(self, trip_id: str, user_id: str, data: Optional[TripShareCreate] = None) -> TripShare:
        trip = self.trip_service.get_trip(trip_id, user_id)

        existing_share = self.share_repo.get_by_trip(trip_id)
        if existing_share:
            # Refresh visibility
            trip.visibility = TripVisibility.PUBLIC
            self.trip_repo.update(trip)
            return existing_share

        share_slug = self._generate_slug()
        while self.share_repo.get_by_slug(share_slug):
            share_slug = self._generate_slug()

        trip.share_slug = share_slug
        trip.visibility = TripVisibility.PUBLIC
        self.trip_repo.update(trip)

        share = TripShare(
            trip_id=trip_id,
            share_slug=share_slug,
            expires_at=data.expires_at if data else None,
        )
        return self.share_repo.create(share)

    def revoke_share(self, trip_id: str, user_id: str) -> None:
        trip = self.trip_service.get_trip(trip_id, user_id)

        share = self.share_repo.get_by_trip(trip_id)
        if share:
            self.share_repo.delete(share)

        trip.share_slug = None
        trip.visibility = TripVisibility.PRIVATE
        self.trip_repo.update(trip)

    def get_public_trip(self, share_slug: str) -> Trip:
        trip = self.trip_repo.get_public_by_slug(share_slug)
        if not trip:
            raise NotFoundError("Shared Trip")

        share = self.share_repo.get_by_slug(share_slug)
        if share:
            if share.expires_at and share.expires_at < datetime.now(UTC):
                raise ValidationError("This share link has expired")
            self.share_repo.increment_view_count(share_slug)

        return trip

    def copy_trip(self, share_slug: str, user_id: str) -> Trip:
        original_trip = self.get_public_trip(share_slug)

        # Create new trip for the current user
        new_trip = Trip(
            user_id=user_id,
            name=f"{original_trip.name} (Copy)",
            description=original_trip.description,
            cover_photo_path=original_trip.cover_photo_path,
            start_date=original_trip.start_date,
            end_date=original_trip.end_date,
            total_budget=original_trip.total_budget,
            visibility=TripVisibility.PRIVATE,
        )
        new_trip = self.trip_repo.create(new_trip)

        # Copy all stops and activities
        for stop in original_trip.stops:
            new_stop = Stop(
                trip_id=new_trip.id,
                city_id=stop.city_id,
                arrival_date=stop.arrival_date,
                departure_date=stop.departure_date,
                stop_order=stop.stop_order,
                notes=stop.notes,
            )
            new_stop = self.stop_repo.create(new_stop)

            for activity in stop.activities:
                new_act = Activity(
                    stop_id=new_stop.id,
                    name=activity.name,
                    description=activity.description,
                    activity_type=activity.activity_type,
                    start_time=activity.start_time,
                    end_time=activity.end_time,
                    estimated_cost=activity.estimated_cost,
                    currency=activity.currency,
                    location_name=activity.location_name,
                    latitude=activity.latitude,
                    longitude=activity.longitude,
                )
                self.activity_repo.create(new_act)

        # Log the copy relation
        copy_record = TripCopy(
            original_trip_id=original_trip.id,
            copied_trip_id=new_trip.id,
            copied_by_user_id=user_id,
        )
        self.copy_repo.create(copy_record)

        return self.trip_repo.get_with_relations(new_trip.id) or new_trip