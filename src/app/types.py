"""Type definitions for the application using Literal types."""

from typing import Literal

# User status types
UserStatus = Literal["active", "inactive", "banned"]

# Driver approval status types
DriverApprovalStatus = Literal["pending", "approved", "rejected"]

# Admin access level types
AdminAccessLevel = Literal["normal", "superuser"]

# Trip type types
TripType = Literal["urban", "intercity", "shared", "economy"]

# Trip status types
TripStatus = Literal["pending", "completed", "canceled", "started", "waiting", "failed"]

# Payment type types
PaymentType = Literal["cash", "electronic"]

# Payment status types
PaymentStatus = Literal["pending", "completed", "failed", "canceled"]

# Discount code type types
DiscountCodeType = Literal["amount", "percent"]

# Discount code status types
DiscountCodeStatus = Literal["used", "expired", "active"]

# Driver application status types
DriverApplicationStatus = Literal["pending", "accepted", "rejected"]

# Document type types
DocumentType = Literal["license", "car_registration", "insurance", "identity", "other"]

# Document status types
DocumentStatus = Literal["pending", "approved", "rejected"]

# Transaction type types
TransactionType = Literal["deposit", "withdraw", "trip_payment", "refund", "adjustment"]

# Trip status history status types
TripStatusHistoryStatus = Literal["pending", "started", "waiting", "completed",
                                  "canceled", "failed", "reopened"]
