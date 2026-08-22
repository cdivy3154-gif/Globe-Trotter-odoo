from datetime import datetime, timedelta, UTC
from typing import Optional, List
from sqlalchemy.orm import Session
from app.core.exceptions import NotFoundError, ForbiddenError, ValidationError
from app.repositories import TripRepository, StopRepository, ActivityRepository, CityRepository
from app.models.trip import Trip, Stop, TripVisibility
from app.models.activity import Activity
from app.schemas.trip import TripCreate, TripUpdate, StopCreate, StopUpdate, ActivityCreate, ActivityUpdate


def _norm_dt(dt: datetime) -> datetime:
    """Normalize datetime to UTC-aware datetime for safe comparisons across SQLite drivers."""
    if dt is None:
        return dt
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class TripService:
    def __init__(self, session: Session):
        self.session = session
        self.trip_repo = TripRepository(session)
        self.stop_repo = StopRepository(session)
        self.activity_repo = ActivityRepository(session)
        self.city_repo = CityRepository(session)

    def create_trip(self, user_id: str, data: TripCreate) -> Trip:
        s_date = _norm_dt(data.start_date)
        e_date = _norm_dt(data.end_date)
        if s_date > e_date:
            raise ValidationError("Start date cannot be after end date")

        trip = Trip(
            user_id=user_id,
            name=data.name.strip(),
            description=data.description.strip() if data.description else None,
            cover_photo_path=data.cover_photo_path,
            start_date=s_date,
            end_date=e_date,
            total_budget=data.total_budget,
            currency=data.currency or "USD",
            visibility=TripVisibility.PRIVATE,
        )
        return self.trip_repo.create(trip)

    def get_trip(self, trip_id: str, user_id: Optional[str] = None) -> Trip:
        trip = self.trip_repo.get_with_relations(trip_id)
        if not trip:
            raise NotFoundError("Trip")
        if user_id and trip.user_id != user_id and trip.visibility != TripVisibility.PUBLIC:
            raise ForbiddenError("Not authorized to access this private trip")
        return trip

    def get_trip_public(self, share_slug: str) -> Trip:
        trip = self.trip_repo.get_public_by_slug(share_slug)
        if not trip:
            raise NotFoundError("Public Trip")
        return trip

    def list_trips(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Trip]:
        return self.trip_repo.get_by_user(user_id, skip, limit)

    def update_trip(self, trip_id: str, user_id: str, data: TripUpdate) -> Trip:
        trip = self.get_trip(trip_id, user_id)

        if data.name is not None:
            trip.name = data.name.strip()
        if data.description is not None:
            trip.description = data.description.strip() if data.description else None
        if data.start_date is not None:
            trip.start_date = _norm_dt(data.start_date)
        if data.end_date is not None:
            trip.end_date = _norm_dt(data.end_date)
        if data.cover_photo_path is not None:
            trip.cover_photo_path = data.cover_photo_path
        if data.total_budget is not None:
            trip.total_budget = data.total_budget
        if data.currency is not None:
            trip.currency = data.currency
        if data.visibility is not None:
            trip.visibility = TripVisibility(data.visibility)

        if _norm_dt(trip.start_date) > _norm_dt(trip.end_date):
            raise ValidationError("Start date cannot be after end date")

        return self.trip_repo.update(trip)

    def delete_trip(self, trip_id: str, user_id: str) -> None:
        trip = self.get_trip(trip_id, user_id)
        self.trip_repo.delete(trip)

    # ----------------- Stops -----------------
    def add_stop(self, trip_id: str, user_id: str, data: StopCreate) -> Stop:
        trip = self.get_trip(trip_id, user_id)

        city = self.city_repo.get(data.city_id)
        if not city:
            raise NotFoundError("City")

        arr_date = _norm_dt(data.arrival_date)
        dep_date = _norm_dt(data.departure_date)

        if arr_date > dep_date:
            raise ValidationError("Arrival date cannot be after departure date")

        # Automatically adjust trip start/end date if stop extends beyond
        trip_start = _norm_dt(trip.start_date)
        trip_end = _norm_dt(trip.end_date)

        if arr_date < trip_start:
            trip.start_date = arr_date
            self.trip_repo.update(trip)
        if dep_date > trip_end:
            trip.end_date = dep_date
            self.trip_repo.update(trip)

        max_order = self.stop_repo.get_max_order(trip_id)
        stop = Stop(
            trip_id=trip_id,
            city_id=data.city_id,
            arrival_date=arr_date,
            departure_date=dep_date,
            stop_order=data.stop_order or (max_order + 1),
            notes=data.notes,
        )
        created_stop = self.stop_repo.create(stop)
        return self.stop_repo.get_with_relations(created_stop.id) or created_stop

    def update_stop(self, trip_id: str, user_id: str, stop_id: str, data: StopUpdate) -> Stop:
        trip = self.get_trip(trip_id, user_id)
        stop = self.stop_repo.get_with_relations(stop_id)
        if not stop or stop.trip_id != trip_id:
            raise NotFoundError("Stop")

        if data.arrival_date is not None:
            stop.arrival_date = _norm_dt(data.arrival_date)
        if data.departure_date is not None:
            stop.departure_date = _norm_dt(data.departure_date)
        if data.stop_order is not None:
            stop.stop_order = data.stop_order
        if data.notes is not None:
            stop.notes = data.notes

        if _norm_dt(stop.arrival_date) > _norm_dt(stop.departure_date):
            raise ValidationError("Arrival date cannot be after departure date")

        self.stop_repo.update(stop)
        return self.stop_repo.get_with_relations(stop.id) or stop

    def delete_stop(self, trip_id: str, user_id: str, stop_id: str) -> None:
        self.get_trip(trip_id, user_id)
        stop = self.stop_repo.get(stop_id)
        if not stop or stop.trip_id != trip_id:
            raise NotFoundError("Stop")
        self.stop_repo.delete(stop)

    def reorder_stops(self, trip_id: str, user_id: str, stop_orders: List[tuple[str, int]]) -> None:
        self.get_trip(trip_id, user_id)
        self.stop_repo.reorder_stops(trip_id, stop_orders)

    # ----------------- Activities -----------------
    def add_activity(self, trip_id: str, user_id: str, stop_id: str, data: ActivityCreate) -> Activity:
        self.get_trip(trip_id, user_id)
        stop = self.stop_repo.get_with_relations(stop_id)
        if not stop or stop.trip_id != trip_id:
            raise NotFoundError("Stop")

        st = _norm_dt(data.start_time)
        et = _norm_dt(data.end_time)

        if st > et:
            raise ValidationError("Activity start time cannot be after end time")

        activity = Activity(
            stop_id=stop_id,
            name=data.name.strip(),
            description=data.description.strip() if data.description else None,
            activity_type=data.activity_type,
            start_time=st,
            end_time=et,
            estimated_cost=data.estimated_cost or 0.0,
            currency=data.currency,
            location_name=data.location_name,
            latitude=data.latitude,
            longitude=data.longitude,
        )
        return self.activity_repo.create(activity)

    def update_activity(
        self, trip_id: str, user_id: str, stop_id: str, activity_id: str, data: ActivityUpdate
    ) -> Activity:
        self.get_trip(trip_id, user_id)
        stop = self.stop_repo.get(stop_id)
        if not stop or stop.trip_id != trip_id:
            raise NotFoundError("Stop")

        activity = self.activity_repo.get(activity_id)
        if not activity or activity.stop_id != stop_id:
            raise NotFoundError("Activity")

        if data.name is not None:
            activity.name = data.name.strip()
        if data.description is not None:
            activity.description = data.description.strip() if data.description else None
        if data.activity_type is not None:
            activity.activity_type = data.activity_type
        if data.start_time is not None:
            activity.start_time = _norm_dt(data.start_time)
        if data.end_time is not None:
            activity.end_time = _norm_dt(data.end_time)
        if data.estimated_cost is not None:
            activity.estimated_cost = data.estimated_cost
        if data.currency is not None:
            activity.currency = data.currency
        if data.location_name is not None:
            activity.location_name = data.location_name
        if data.latitude is not None:
            activity.latitude = data.latitude
        if data.longitude is not None:
            activity.longitude = data.longitude

        if _norm_dt(activity.start_time) > _norm_dt(activity.end_time):
            raise ValidationError("Activity start time cannot be after end time")

        return self.activity_repo.update(activity)

    def delete_activity(self, trip_id: str, user_id: str, stop_id: str, activity_id: str) -> None:
        self.get_trip(trip_id, user_id)
        stop = self.stop_repo.get(stop_id)
        if not stop or stop.trip_id != trip_id:
            raise NotFoundError("Stop")

        activity = self.activity_repo.get(activity_id)
        if not activity or activity.stop_id != stop_id:
            raise NotFoundError("Activity")
        self.activity_repo.delete(activity)

    # ----------------- Budget Breakdown -----------------
    def get_budget_breakdown(self, trip_id: str, user_id: Optional[str] = None) -> dict:
        trip = self.get_trip(trip_id, user_id)

        total_activities = 0.0
        for stop in trip.stops:
            for activity in stop.activities:
                if activity.estimated_cost:
                    total_activities += float(activity.estimated_cost)

        base_accommodation = 50.0  # per night
        base_meals = 30.0          # per day
        base_transport = 20.0      # per day

        total_accommodation = 0.0
        total_meals = 0.0
        total_transport = 0.0
        overbudget_days = []

        trip_s = _norm_dt(trip.start_date).date()
        trip_e = _norm_dt(trip.end_date).date()
        total_trip_days = max((trip_e - trip_s).days + 1, 1)
        avg_daily_budget = (trip.total_budget / total_trip_days) if (trip.total_budget and trip.total_budget > 0) else None

        for stop in trip.stops:
            city = stop.city
            cost_factor = (city.cost_index / 50.0) if (city and city.cost_index) else 1.0
            stop_arr = _norm_dt(stop.arrival_date).date()
            stop_dep = _norm_dt(stop.departure_date).date()
            stay_days = max((stop_dep - stop_arr).days + 1, 1)
            nights = max(stay_days - 1, 1)

            accom = base_accommodation * cost_factor * nights
            meals = base_meals * cost_factor * stay_days
            transport = base_transport * cost_factor * stay_days

            total_accommodation += accom
            total_meals += meals
            total_transport += transport

            daily_est = (accom + meals + transport) / stay_days
            if avg_daily_budget and daily_est > (avg_daily_budget * 1.3):
                overbudget_days.append(f"{city.name if city else 'Stop'} ({_norm_dt(stop.arrival_date).strftime('%b %d')})")

        total = total_activities + total_accommodation + total_meals + total_transport
        avg_per_day = total / total_trip_days if total_trip_days > 0 else 0.0

        return {
            "transport": round(total_transport, 2),
            "accommodation": round(total_accommodation, 2),
            "activities": round(total_activities, 2),
            "meals": round(total_meals, 2),
            "total": round(total, 2),
            "average_per_day": round(avg_per_day, 2),
            "overbudget_days": overbudget_days,
            "total_budget": trip.total_budget,
            "currency": getattr(trip, "currency", "USD") or "USD",
            "days_count": total_trip_days,
        }

    # ----------------- Calendar/Timeline View -----------------
    def get_calendar(self, trip_id: str, user_id: Optional[str] = None) -> List[dict]:
        trip = self.get_trip(trip_id, user_id)

        days = []
        curr = _norm_dt(trip.start_date).date()
        end = _norm_dt(trip.end_date).date()

        while curr <= end:
            day_stops = [
                s for s in trip.stops
                if _norm_dt(s.arrival_date).date() <= curr <= _norm_dt(s.departure_date).date()
            ]
            day_activities = []
            for s in day_stops:
                for a in s.activities:
                    if _norm_dt(a.start_time).date() <= curr <= _norm_dt(a.end_time).date():
                        day_activities.append(a)

            days.append({
                "date": datetime(curr.year, curr.month, curr.day, tzinfo=UTC),
                "stops": day_stops,
                "activities": day_activities,
            })
            curr += timedelta(days=1)

        return days