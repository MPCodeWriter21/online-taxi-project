"""Payment-related Pydantic schemas."""

from typing import Optional
from decimal import Decimal
from datetime import datetime

from pydantic import Field, BaseModel

from ..types import PaymentType, PaymentStatus, TransactionType


class PaymentBase(BaseModel):
    """Base payment schema."""

    amount: Decimal = Field(..., ge=0)
    payment_type: Optional[PaymentType] = None


class PaymentCreate(PaymentBase):
    """Schema for creating a payment."""

    pass


class PaymentUpdate(BaseModel):
    """Schema for updating a payment."""

    status: Optional[PaymentStatus] = None


class PaymentResponse(PaymentBase):
    """Schema for payment response."""

    id: int
    payment_date: datetime
    status: Optional[PaymentStatus]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransactionBase(BaseModel):
    """Base transaction schema."""

    user_id: int
    amount: Decimal = Field(..., ne=0)
    type: TransactionType
    payment_id: Optional[int] = None


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction."""

    pass


class TransactionResponse(TransactionBase):
    """Schema for transaction response."""

    id: int
    date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WalletBalanceResponse(BaseModel):
    """Schema for wallet balance response."""

    user_id: int
    balance: Decimal


class WalletTopUpRequest(BaseModel):
    """Schema for wallet top-up request."""

    amount: Decimal = Field(..., gt=0)
    payment_type: PaymentType
