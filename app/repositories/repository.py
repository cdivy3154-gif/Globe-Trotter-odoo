from typing import Optional, List
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, and_
from app.repositories.base import BaseRepository
from app.models.user import User
from app.models.trip import Trip, Stop, TripVisibility
from app.models.activity import Activity
from app.models.city import City, ActivityCatalog
from app.models.sharing import TripShare, TripCopy, UserSavedDestination


class UserRepository(BaseRepository[User]):
    def __init__(self, session: Session):
        super().__init__(User, session)

    def get_by_email(self, email: str) -> Optional[User]:
        result = self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    def get_by_id_with_relations(self, id: str) -> Optional[User]:
        result = self.session.execute(
            select(User)
            .options(
                selectinload(User.trips),
                selectinload(User.saved_destinations),
                selectinload(User.copied_trips)
            )
            .where(User.id == id)
        )
        return result.scalar_one_or_none()


class TripRepository(BaseRepository[Trip]):
    def __init__(self, session: Session):
        super().__init__(Trip, session)

    def get_by_user(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Trip]:
        result = self.session.execute(
            select(Trip)
            .options(
                selectinload(Trip.stops).selectinload(Stop.city),
                selectinload(Trip.stops).selectinload(Stop.activities)
            )
            .where(Trip.user_id == user_id)
            .order_by(Trip.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    def get_with_relations(self, trip_id: str) -> Optional[Trip]:
        result = self.session.execute(
            select(Trip)
            .options(
                selectinload(Trip.stops).selectinload(Stop.city),
                selectinload(Trip.stops).selectinload(Stop.activities),
                selectinload(Trip.user),
                selectinload(Trip.share)
            )
            .where(Trip.id == trip_id)
        )
        return result.scalar_one_or_none()

    def get_public_by_slug(self, share_slug: str) -> Optional[Trip]:
        result = self.session.execute(
            select(Trip)
            .options(
                selectinload(Trip.stops).selectinload(Stop.city),
                selectinload(Trip.stops).selectinload(Stop.activities),
                selectinload(Trip.user)
            )
            .where(Trip.share_slug == share_slug, Trip.visibility == TripVisibility.PUBLIC)
        )
        return result.scalar_one_or_none()

    def count_by_user(self, user_id: str) -> int:
        result = self.session.execute(
            select(func.count(Trip.id)).where(Trip.user_id == user_id)
        )
        return result.scalar_one()


class StopRepository(BaseRepository[Stop]):
    def __init__(self, session: Session):
        super().__init__(Stop, session)

    def get_by_trip(self, trip_id: str) -> List[Stop]:
        result = self.session.execute(
            select(Stop)
            .options(selectinload(Stop.city), selectinload(Stop.activities))
            .where(Stop.trip_id == trip_id)
            .order_by(Stop.stop_order)
        )
        return list(result.scalars().all())

    def get_with_relations(self, stop_id: str) -> Optional[Stop]:
        result = self.session.execute(
            select(Stop)
            .options(
                selectinload(Stop.city),
                selectinload(Stop.activities)
            )
            .where(Stop.id == stop_id)
        )
        return result.scalar_one_or_none()

    def get_max_order(self, trip_id: str) -> int:
        result = self.session.execute(
            select(func.coalesce(func.max(Stop.stop_order), 0)).where(Stop.trip_id == trip_id)
        )
        return result.scalar_one()

    def reorder_stops(self, trip_id: str, stop_orders: List[tuple[str, int]]) -> None:
        for stop_id, order in stop_orders:
            stop = self.session.execute(
                select(Stop).where(Stop.id == stop_id, Stop.trip_id == trip_id)
            ).scalar_one_or_none()
            if stop:
                stop.stop_order = order
        self.session.flush()


class ActivityRepository(BaseRepository[Activity]):
    def __init__(self, session: Session):
        super().__init__(Activity, session)

    def get_by_stop(self, stop_id: str) -> List[Activity]:
        result = self.session.execute(
            select(Activity)
            .where(Activity.stop_id == stop_id)
            .order_by(Activity.start_time)
        )
        return list(result.scalars().all())


class CityRepository(BaseRepository[City]):
    def __init__(self, session: Session):
        super().__init__(City, session)

    def search(
        self,
        q: Optional[str] = None,
        country: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[City]:
        query = select(City)
        conditions = []
        if q:
            conditions.append(City.name.ilike(f"%{q}%"))
        if country:
            conditions.append(City.country.ilike(f"%{country}%"))
        if region:
            conditions.append(City.region.ilike(f"%{region}%"))
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(City.popularity_score.desc()).offset(offset).limit(limit)
        result = self.session.execute(query)
        return list(result.scalars().all())

    def count_search(
        self,
        q: Optional[str] = None,
        country: Optional[str] = None,
        region: Optional[str] = None
    ) -> int:
        query = select(func.count(City.id))
        conditions = []
        if q:
            conditions.append(City.name.ilike(f"%{q}%"))
        if country:
            conditions.append(City.country.ilike(f"%{country}%"))
        if region:
            conditions.append(City.region.ilike(f"%{region}%"))
        if conditions:
            query = query.where(and_(*conditions))
        result = self.session.execute(query)
        return result.scalar_one()

    def get_with_activities(self, city_id: str) -> Optional[City]:
        result = self.session.execute(
            select(City)
            .options(selectinload(City.activities_catalog))
            .where(City.id == city_id)
        )
        return result.scalar_one_or_none()


class ActivityCatalogRepository(BaseRepository[ActivityCatalog]):
    def __init__(self, session: Session):
        super().__init__(ActivityCatalog, session)

    def get_by_city(
        self,
        city_id: Optional[str] = None,
        activity_type: Optional[str] = None,
        cost_min: Optional[float] = None,
        cost_max: Optional[float] = None,
        duration_max: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ActivityCatalog]:
        query = select(ActivityCatalog)
        conditions = []
        if city_id:
            conditions.append(ActivityCatalog.city_id == city_id)
        if activity_type:
            conditions.append(ActivityCatalog.activity_type == activity_type)
        if cost_min is not None:
            conditions.append(ActivityCatalog.avg_cost >= cost_min)
        if cost_max is not None:
            conditions.append(ActivityCatalog.avg_cost <= cost_max)
        if duration_max is not None:
            conditions.append(ActivityCatalog.duration_minutes <= duration_max)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(ActivityCatalog.name).offset(offset).limit(limit)
        result = self.session.execute(query)
        return list(result.scalars().all())

    def count_by_city(
        self,
        city_id: Optional[str] = None,
        activity_type: Optional[str] = None,
        cost_min: Optional[float] = None,
        cost_max: Optional[float] = None,
        duration_max: Optional[int] = None
    ) -> int:
        query = select(func.count(ActivityCatalog.id))
        conditions = []
        if city_id:
            conditions.append(ActivityCatalog.city_id == city_id)
        if activity_type:
            conditions.append(ActivityCatalog.activity_type == activity_type)
        if cost_min is not None:
            conditions.append(ActivityCatalog.avg_cost >= cost_min)
        if cost_max is not None:
            conditions.append(ActivityCatalog.avg_cost <= cost_max)
        if duration_max is not None:
            conditions.append(ActivityCatalog.duration_minutes <= duration_max)
        if conditions:
            query = query.where(and_(*conditions))
        result = self.session.execute(query)
        return result.scalar_one()


class TripShareRepository(BaseRepository[TripShare]):
    def __init__(self, session: Session):
        super().__init__(TripShare, session)

    def get_by_trip(self, trip_id: str) -> Optional[TripShare]:
        result = self.session.execute(
            select(TripShare).where(TripShare.trip_id == trip_id)
        )
        return result.scalar_one_or_none()

    def get_by_slug(self, share_slug: str) -> Optional[TripShare]:
        result = self.session.execute(
            select(TripShare).where(TripShare.share_slug == share_slug)
        )
        return result.scalar_one_or_none()

    def increment_view_count(self, share_slug: str) -> None:
        share = self.get_by_slug(share_slug)
        if share:
            share.view_count += 1
            self.session.flush()


class TripCopyRepository(BaseRepository[TripCopy]):
    def __init__(self, session: Session):
        super().__init__(TripCopy, session)

    def get_by_original(self, original_trip_id: str) -> List[TripCopy]:
        result = self.session.execute(
            select(TripCopy).where(TripCopy.original_trip_id == original_trip_id)
        )
        return list(result.scalars().all())

    def get_by_copied(self, copied_trip_id: str) -> Optional[TripCopy]:
        result = self.session.execute(
            select(TripCopy).where(TripCopy.copied_trip_id == copied_trip_id)
        )
        return result.scalar_one_or_none()


class UserSavedDestinationRepository(BaseRepository[UserSavedDestination]):
    def __init__(self, session: Session):
        super().__init__(UserSavedDestination, session)

    def get_by_user(self, user_id: str) -> List[UserSavedDestination]:
        result = self.session.execute(
            select(UserSavedDestination)
            .options(selectinload(UserSavedDestination.city))
            .where(UserSavedDestination.user_id == user_id)
        )
        return list(result.scalars().all())

    def exists(self, user_id: str, city_id: str) -> bool:
        result = self.session.execute(
            select(UserSavedDestination)
            .where(
                UserSavedDestination.user_id == user_id,
                UserSavedDestination.city_id == city_id
            )
        )
        return result.scalar_one_or_none() is not None