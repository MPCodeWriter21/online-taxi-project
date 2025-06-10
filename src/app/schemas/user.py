"""User-related Pydantic schemas."""

from typing import Optional
from decimal import Decimal
from datetime import datetime

from pydantic import Field, EmailStr, BaseModel

from ..types import UserStatus, AdminAccessLevel, DriverApprovalStatus


class UserBase(BaseModel):
    """Base user schema."""

    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., min_length=10, max_length=20)
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    status: Optional[UserStatus] = None


class UserResponse(UserBase):
    """Schema for user response."""

    id: int
    registration_date: datetime
    wallet_balance: Decimal
    status: Optional[UserStatus]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DriverBase(BaseModel):
    """Base driver schema."""

    license_number: Optional[str] = Field(None, max_length=50)
    car_info: Optional[dict] = None


class DriverCreate(DriverBase):
    """Schema for creating a driver."""

    user_id: int


class DriverUpdate(DriverBase):
    """Schema for updating a driver."""

    approval_status: Optional[DriverApprovalStatus] = None


class DriverResponse(DriverBase):
    """Schema for driver response."""

    user_id: int
    approval_status: Optional[DriverApprovalStatus]
    created_at: datetime
    updated_at: datetime
    user: UserResponse

    class Config:
        from_attributes = True


class AdminBase(BaseModel):
    """Base admin schema."""

    access_level: Optional[AdminAccessLevel] = None


class AdminCreate(AdminBase):
    """Schema for creating an admin."""

    user_id: int


class AdminUpdate(AdminBase):
    """Schema for updating an admin."""

    pass


class AdminResponse(AdminBase):
    """Schema for admin response."""

    user_id: int
    access_level: Optional[AdminAccessLevel]
    created_at: datetime
    updated_at: datetime
    user: UserResponse

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Schema for login request."""

    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Schema for login response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
