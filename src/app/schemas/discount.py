"""Discount-related Pydantic schemas."""

from typing import Optional
from decimal import Decimal
from datetime import date, datetime

from pydantic import Field, BaseModel

from ..types import DiscountCodeType, DiscountCodeStatus


class DiscountCodeBase(BaseModel):
    """Base discount code schema."""

    code: str = Field(..., min_length=1, max_length=50)
    value: Decimal = Field(..., gt=0)
    type: DiscountCodeType
    expiry_date: Optional[date] = None


class DiscountCodeCreate(DiscountCodeBase):
    """Schema for creating a discount code."""

    pass


class DiscountCodeUpdate(BaseModel):
    """Schema for updating a discount code."""

    value: Optional[Decimal] = Field(None, gt=0)
    expiry_date: Optional[date] = None
    status: Optional[DiscountCodeStatus] = None


class DiscountCodeResponse(DiscountCodeBase):
    """Schema for discount code response."""

    id: int
    status: Optional[DiscountCodeStatus]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DiscountUserBase(BaseModel):
    """Base discount user mapping schema."""

    discount_code_id: int
    user_id: int


class DiscountUserCreate(DiscountUserBase):
    """Schema for creating a discount user mapping."""

    pass


class DiscountUserResponse(DiscountUserBase):
    """Schema for discount user mapping response."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplyDiscountRequest(BaseModel):
    """Schema for applying discount code."""

    code: str = Field(..., min_length=1)
    trip_amount: Decimal = Field(..., gt=0)


class ApplyDiscountResponse(BaseModel):
    """Schema for discount application response."""

    valid: bool
    discount_amount: Decimal = 0
    final_amount: Decimal
    message: str
