from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class TopCityStat(BaseModel):
    city_id: str
    city_name: str
    country: str
    trip_count: int


class TopActivityStat(BaseModel):
    activity_type: str
    count: int


class AdminStatsResponse(BaseModel):
    total_users: int
    total_trips: int
    total_cities: int
    total_activities: int
    top_cities: List[TopCityStat] = []
    top_activities: List[TopActivityStat] = []
    recent_trips: int


class AdminUserListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: Optional[str] = None
    role: str
    created_at: datetime
    trip_count: int = 0


class AdminTripListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    user_id: str
    user_email: str
    start_date: datetime
    end_date: datetime
    destination_count: int
    visibility: str
    created_at: datetime