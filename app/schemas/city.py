from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class CityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    country: str = Field(..., min_length=1, max_length=255)
    country_code: str = Field(..., min_length=2, max_length=2)
    region: Optional[str] = Field(None, max_length=255)
    timezone: str = Field(default="UTC", max_length=100)
    cost_index: int = Field(default=50, ge=1, le=100)
    popularity_score: int = Field(default=0, ge=0)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None


class CityCreate(CityBase):
    pass


class CityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    country: Optional[str] = Field(None, min_length=1, max_length=255)
    country_code: Optional[str] = Field(None, min_length=2, max_length=2)
    region: Optional[str] = Field(None, max_length=255)
    timezone: Optional[str] = Field(None, max_length=100)
    cost_index: Optional[int] = Field(None, ge=1, le=100)
    popularity_score: Optional[int] = Field(None, ge=0)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None


class CityResponse(CityBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime


class CitySearchParams(BaseModel):
    q: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class ActivityCatalogBase(BaseModel):
    city_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    activity_type: str = Field(..., min_length=1, max_length=100)
    avg_cost: Optional[float] = Field(None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    duration_minutes: Optional[int] = Field(None, ge=0)
    tags: List[str] = []
    image_url: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ActivityCatalogCreate(ActivityCatalogBase):
    pass


class ActivityCatalogUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    activity_type: Optional[str] = Field(None, min_length=1, max_length=100)
    avg_cost: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    duration_minutes: Optional[int] = Field(None, ge=0)
    tags: Optional[List[str]] = None
    image_url: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ActivityCatalogResponse(ActivityCatalogBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source: str
    external_id: Optional[str] = None
    created_at: datetime


class ActivitySearchParams(BaseModel):
    city_id: Optional[str] = None
    activity_type: Optional[str] = None
    cost_min: Optional[float] = Field(None, ge=0)
    cost_max: Optional[float] = Field(None, ge=0)
    duration_max: Optional[int] = Field(None, ge=0)
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)