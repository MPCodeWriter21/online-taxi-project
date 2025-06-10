"""Schemas __init__.py file."""

# yapf: disable

from .trip import (TripBase, RouteBase, TariffBase, TripCreate, TripUpdate, RouteCreate,
                   RouteUpdate, TariffCreate, TariffUpdate, TripResponse, RouteResponse,
                   TariffResponse, TripSearchRequest, TripEstimateResponse)
from .user import (UserBase, AdminBase, DriverBase, UserCreate, UserUpdate, AdminCreate,
                   AdminUpdate, DriverCreate, DriverUpdate, LoginRequest, UserResponse,
                   AdminResponse, LoginResponse, DriverResponse)
from .payment import (PaymentBase, PaymentCreate, PaymentUpdate, PaymentResponse,
                      TransactionBase, TransactionCreate, WalletTopUpRequest,
                      TransactionResponse, WalletBalanceResponse)
from .discount import (DiscountCodeBase, DiscountUserBase, DiscountCodeCreate,
                       DiscountCodeUpdate, DiscountUserCreate, ApplyDiscountRequest,
                       DiscountCodeResponse, DiscountUserResponse,
                       ApplyDiscountResponse)
from .location import (CityBase, CityCreate, CityUpdate, CityResponse, ProvinceBase,
                       ProvinceCreate, ProvinceUpdate, ProvinceResponse)

# yapf: enable

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "DriverBase",
    "DriverCreate",
    "DriverUpdate",
    "DriverResponse",
    "AdminBase",
    "AdminCreate",
    "AdminUpdate",
    "AdminResponse",
    "LoginRequest",
    "LoginResponse",
    # Trip schemas
    "RouteBase",
    "RouteCreate",
    "RouteUpdate",
    "RouteResponse",
    "TariffBase",
    "TariffCreate",
    "TariffUpdate",
    "TariffResponse",
    "TripBase",
    "TripCreate",
    "TripUpdate",
    "TripResponse",
    "TripSearchRequest",
    "TripEstimateResponse",
    # Payment schemas
    "PaymentBase",
    "PaymentCreate",
    "PaymentUpdate",
    "PaymentResponse",
    "TransactionBase",
    "TransactionCreate",
    "TransactionResponse",
    "WalletBalanceResponse",
    "WalletTopUpRequest",
    # Location schemas
    "ProvinceBase",
    "ProvinceCreate",
    "ProvinceUpdate",
    "ProvinceResponse",
    "CityBase",
    "CityCreate",
    "CityUpdate",
    "CityResponse",
    # Discount schemas
    "DiscountCodeBase",
    "DiscountCodeCreate",
    "DiscountCodeUpdate",
    "DiscountCodeResponse",
    "DiscountUserBase",
    "DiscountUserCreate",
    "DiscountUserResponse",
    "ApplyDiscountRequest",
    "ApplyDiscountResponse",
]
