from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.core.exceptions import NotFoundError
from app.repositories import CityRepository, ActivityCatalogRepository, UserSavedDestinationRepository
from app.models.city import City, ActivityCatalog
from app.models.sharing import UserSavedDestination
from app.schemas.city import CityCreate, CityUpdate, ActivityCatalogCreate, ActivityCatalogUpdate, CitySearchParams, ActivitySearchParams


class CityService:
    def __init__(self, session: Session):
        self.session = session
        self.city_repo = CityRepository(session)
        self.activity_catalog_repo = ActivityCatalogRepository(session)
        self.saved_dest_repo = UserSavedDestinationRepository(session)

    def search_cities(self, params: CitySearchParams) -> Tuple[List[City], int]:
        cities = self.city_repo.search(
            q=params.q,
            country=params.country,
            region=params.region,
            limit=params.limit,
            offset=params.offset,
        )
        total = self.city_repo.count_search(
            q=params.q,
            country=params.country,
            region=params.region,
        )
        return cities, total

    def get_city(self, city_id: str) -> City:
        city = self.city_repo.get(city_id)
        if not city:
            raise NotFoundError("City")
        return city

    def get_city_with_activities(self, city_id: str) -> City:
        city = self.city_repo.get_with_activities(city_id)
        if not city:
            raise NotFoundError("City")
        return city

    def create_city(self, data: CityCreate) -> City:
        city = City(**data.model_dump())
        return self.city_repo.create(city)

    def update_city(self, city_id: str, data: CityUpdate) -> City:
        city = self.get_city(city_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(city, field, value)
        return self.city_repo.update(city)

    def delete_city(self, city_id: str) -> None:
        city = self.get_city(city_id)
        self.city_repo.delete(city)

    def search_activities(self, params: ActivitySearchParams) -> Tuple[List[ActivityCatalog], int]:
        activities = self.activity_catalog_repo.get_by_city(
            city_id=params.city_id,
            activity_type=params.activity_type,
            cost_min=params.cost_min,
            cost_max=params.cost_max,
            duration_max=params.duration_max,
            limit=params.limit,
            offset=params.offset,
        )
        total = self.activity_catalog_repo.count_by_city(
            city_id=params.city_id,
            activity_type=params.activity_type,
            cost_min=params.cost_min,
            cost_max=params.cost_max,
            duration_max=params.duration_max,
        )
        return activities, total

    def get_activity(self, activity_id: str) -> ActivityCatalog:
        activity = self.activity_catalog_repo.get(activity_id)
        if not activity:
            raise NotFoundError("Activity")
        return activity

    def create_activity(self, data: ActivityCatalogCreate) -> ActivityCatalog:
        self.get_city(data.city_id)
        activity = ActivityCatalog(**data.model_dump())
        return self.activity_catalog_repo.create(activity)

    def update_activity(self, activity_id: str, data: ActivityCatalogUpdate) -> ActivityCatalog:
        activity = self.get_activity(activity_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(activity, field, value)
        return self.activity_catalog_repo.update(activity)

    def delete_activity(self, activity_id: str) -> None:
        activity = self.get_activity(activity_id)
        self.activity_catalog_repo.delete(activity)

    # ---------------- Saved Destinations ----------------
    def toggle_save_destination(self, user_id: str, city_id: str) -> bool:
        """Save or unsave a destination for a user. Returns True if now saved, False if removed."""
        self.get_city(city_id)
        existing = self.session.query(UserSavedDestination).filter_by(
            user_id=user_id, city_id=city_id
        ).first()

        if existing:
            self.saved_dest_repo.delete(existing)
            return False
        else:
            saved = UserSavedDestination(user_id=user_id, city_id=city_id)
            self.saved_dest_repo.create(saved)
            return True

    def get_saved_destinations(self, user_id: str) -> List[UserSavedDestination]:
        return self.saved_dest_repo.get_by_user(user_id)