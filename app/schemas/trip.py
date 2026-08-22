from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class TripBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    total_budget: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field("USD", min_length=3, max_length=3)


class TripCreate(TripBase):
    cover_photo_path: Optional[str] = Field(None, max_length=500)


class TripUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    cover_photo_path: Optional[str] = Field(None, max_length=500)
    total_budget: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    visibility: Optional[str] = Field(None, pattern="^(private|public)$")


class ActivityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    activity_type: str = Field(..., min_length=1, max_length=100)
    start_time: datetime
    end_time: datetime
    estimated_cost: Optional[float] = Field(None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    location_name: Optional[str] = Field(None, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    activity_type: Optional[str] = Field(None, min_length=1, max_length=100)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    estimated_cost: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    location_name: Optional[str] = Field(None, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ActivityResponse(ActivityBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    stop_id: str
    created_at: datetime


class StopBase(BaseModel):
    city_id: str
    arrival_date: datetime
    departure_date: datetime
    stop_order: int = 1
    notes: Optional[str] = None


class StopCreate(StopBase):
    pass


class StopUpdate(BaseModel):
    arrival_date: Optional[datetime] = None
    departure_date: Optional[datetime] = None
    stop_order: Optional[int] = None
    notes: Optional[str] = None


class StopReorder(BaseModel):
    stop_id: str
    stop_order: int


class StopResponse(StopBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    trip_id: str
    created_at: datetime
    city: Optional[dict] = None
    activities: List[ActivityResponse] = []


class TripResponse(TripBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    cover_photo_path: Optional[str] = None
    visibility: str
    share_slug: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    stops: List[StopResponse] = []


class TripListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    cover_photo_path: Optional[str] = None
    start_date: datetime
    end_date: datetime
    destination_count: int = 0
    visibility: str = "private"
    total_budget: Optional[float] = None
    created_at: datetime


class BudgetBreakdown(BaseModel):
    transport: float = 0.0
    accommodation: float = 0.0
    activities: float = 0.0
    meals: float = 0.0
    total: float = 0.0
    average_per_day: float = 0.0
    overbudget_days: List[str] = []


class CalendarDay(BaseModel):
    date: datetime
    stops: List[dict] = []
    activities: List[dict] = []