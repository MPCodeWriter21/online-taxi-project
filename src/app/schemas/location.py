"""Location-related Pydantic schemas."""

from typing import Optional
from datetime import datetime

from pydantic import Field, BaseModel


class ProvinceBase(BaseModel):
    """Base province schema."""

    name: str = Field(..., min_length=1, max_length=100)


class ProvinceCreate(ProvinceBase):
    """Schema for creating a province."""

    pass


class ProvinceUpdate(ProvinceBase):
    """Schema for updating a province."""

    pass


class ProvinceResponse(ProvinceBase):
    """Schema for province response."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CityBase(BaseModel):
    """Base city schema."""

    name: str = Field(..., min_length=1, max_length=100)
    province_id: int
    coverage_status: bool = True


class CityCreate(CityBase):
    """Schema for creating a city."""

    pass


class CityUpdate(BaseModel):
    """Schema for updating a city."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    coverage_status: Optional[bool] = None


class CityResponse(CityBase):
    """Schema for city response."""

    id: int
    created_at: datetime
    updated_at: datetime
    province: Optional[ProvinceResponse] = None

    class Config:
        from_attributes = True
