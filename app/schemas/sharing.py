from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class TripShareCreate(BaseModel):
    expires_at: Optional[datetime] = None


class TripShareResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    trip_id: str
    share_slug: str
    view_count: int
    created_at: datetime
    expires_at: Optional[datetime] = None


class PublicActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    activity_type: str
    start_time: datetime
    end_time: datetime
    estimated_cost: Optional[float] = None
    currency: str = "USD"
    location_name: Optional[str] = None


class PublicStopResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    city_id: str
    arrival_date: datetime
    departure_date: datetime
    stop_order: int
    notes: Optional[str] = None
    city_name: Optional[str] = None
    country: Optional[str] = None
    activities: List[PublicActivityResponse] = []


class PublicTripResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    cover_photo_path: Optional[str] = None
    start_date: datetime
    end_date: datetime
    share_slug: Optional[str] = None
    stops: List[PublicStopResponse] = []


class TripCopyRequest(BaseModel):
    pass


class TripCopyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_trip_id: str
    copied_trip_id: str
    copied_by_user_id: str
    created_at: datetime