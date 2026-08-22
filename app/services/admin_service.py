from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from app.models.user import User, UserRole
from app.models.trip import Trip, Stop
from app.models.activity import Activity
from app.models.city import City, ActivityCatalog
from app.schemas.admin import AdminStatsResponse, TopCityStat, TopActivityStat, AdminUserListResponse, AdminTripListResponse


class AdminService:
    def __init__(self, session: Session):
        self.session = session

    def get_stats(self) -> AdminStatsResponse:
        total_users = self.session.execute(select(func.count(User.id))).scalar_one()
        total_trips = self.session.execute(select(func.count(Trip.id))).scalar_one()
        total_cities = self.session.execute(select(func.count(City.id))).scalar_one()
        total_activities = self.session.execute(select(func.count(Activity.id))).scalar_one() + \
                           self.session.execute(select(func.count(ActivityCatalog.id))).scalar_one()

        # Top visited cities based on stops count
        top_city_rows = self.session.execute(
            select(City.id, City.name, City.country, func.count(Stop.id).label("cnt"))
            .join(Stop, Stop.city_id == City.id)
            .group_by(City.id, City.name, City.country)
            .order_by(desc("cnt"))
            .limit(5)
        ).all()

        top_cities = [
            TopCityStat(city_id=str(row[0]), city_name=row[1], country=row[2], trip_count=row[3])
            for row in top_city_rows
        ]

        # Top activity types
        top_act_rows = self.session.execute(
            select(Activity.activity_type, func.count(Activity.id).label("cnt"))
            .group_by(Activity.activity_type)
            .order_by(desc("cnt"))
            .limit(5)
        ).all()

        top_activities = [
            TopActivityStat(activity_type=row[0], count=row[1])
            for row in top_act_rows
        ]

        return AdminStatsResponse(
            total_users=total_users,
            total_trips=total_trips,
            total_cities=total_cities,
            total_activities=total_activities,
            top_cities=top_cities,
            top_activities=top_activities,
            recent_trips=total_trips,
        )

    def list_users(self, skip: int = 0, limit: int = 50) -> List[AdminUserListResponse]:
        users = self.session.execute(
            select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        ).scalars().all()

        result = []
        for u in users:
            trip_count = len(u.trips)
            result.append(
                AdminUserListResponse(
                    id=u.id,
                    email=u.email,
                    full_name=u.full_name,
                    role=u.role.value if hasattr(u.role, "value") else str(u.role),
                    created_at=u.created_at,
                    trip_count=trip_count,
                )
            )
        return result

    def list_all_trips(self, skip: int = 0, limit: int = 50) -> List[AdminTripListResponse]:
        trips = self.session.execute(
            select(Trip).order_by(Trip.created_at.desc()).offset(skip).limit(limit)
        ).scalars().all()

        result = []
        for t in trips:
            result.append(
                AdminTripListResponse(
                    id=t.id,
                    name=t.name,
                    user_id=t.user_id,
                    user_email=t.user.email if t.user else "Unknown",
                    start_date=t.start_date,
                    end_date=t.end_date,
                    destination_count=len(t.stops),
                    visibility=t.visibility.value if hasattr(t.visibility, "value") else str(t.visibility),
                    created_at=t.created_at,
                )
            )
        return result
