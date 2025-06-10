"""Trip-related Pydantic schemas."""

from typing import Optional
from decimal import Decimal
from datetime import datetime

from pydantic import Field, BaseModel

from ..types import TripType, TripStatus
from ..models import Coordinate


class RouteBase(BaseModel):
    """Base route schema."""

    start_city_id: Optional[int] = None
    end_city_id: Optional[int] = None
    start_location: Optional[Coordinate] = None
    end_location: Optional[Coordinate] = None
    is_return: Optional[bool] = False
    distance_km: Optional[Decimal] = Field(None, ge=0)


class RouteCreate(RouteBase):
    """Schema for creating a route."""

    pass


class RouteUpdate(RouteBase):
    """Schema for updating a route."""

    pass


class RouteResponse(RouteBase):
    """Schema for route response."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TariffBase(BaseModel):
    """Base tariff schema."""

    city_id: Optional[int] = None
    trip_type: Optional[TripType] = None
    price_per_km: Decimal = Field(..., ge=0)


class TariffCreate(TariffBase):
    """Schema for creating a tariff."""

    pass


class TariffUpdate(TariffBase):
    """Schema for updating a tariff."""

    pass


class TariffResponse(TariffBase):
    """Schema for tariff response."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TripBase(BaseModel):
    """Base trip schema."""

    passenger_id: int
    driver_id: Optional[int] = None
    route_id: Optional[int] = None
    trip_type: Optional[TripType] = None
    discount_code_id: Optional[int] = None
    start_location: Optional[Coordinate] = None
    end_location: Optional[Coordinate] = None


class TripCreate(TripBase):
    """Schema for creating a trip."""

    pass


class TripUpdate(BaseModel):
    """Schema for updating a trip."""

    driver_id: Optional[int] = None
    trip_status: Optional[TripStatus] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    payment_id: Optional[int] = None


class TripResponse(TripBase):
    """Schema for trip response."""

    id: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    trip_status: Optional[TripStatus]
    payment_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TripSearchRequest(BaseModel):
    """Schema for trip search request."""

    start_location: Coordinate
    end_location: Coordinate
    trip_type: Optional[TripType] = "urban"


class TripEstimateResponse(BaseModel):
    """Schema for trip estimate response."""

    estimated_distance_km: Decimal
    estimated_price: Decimal
    estimated_duration_minutes: int
    available_drivers: int
