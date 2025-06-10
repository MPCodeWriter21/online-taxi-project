"""User API v1 endpoints."""

# yapf: disable

from typing import List

from fastapi import Depends, APIRouter, HTTPException, status

from app.core.db import Database
from app.dependencies import get_current_user, get_current_user_optional
from app.schemas.trip import TripResponse, TripSearchRequest, TripEstimateResponse
from app.schemas.user import (UserCreate, UserUpdate, LoginRequest, UserResponse,
                              LoginResponse)
from app.core.security import create_jwt_token
from app.schemas.payment import WalletTopUpRequest, WalletBalanceResponse
from app.services.trip_service import TripService
from app.services.user_service import UserService
from app.services.payment_service import TransactionService

# yapf: enable

router = APIRouter(tags=["user-api-v1"], prefix="/api/v1")


@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Database):
    """Register a new user."""
    return await UserService.create_user(db, user_data)


@router.post("/login", response_model=LoginResponse)
async def login_user(login_data: LoginRequest, db: Database):
    """Login user and return access token."""
    user = await UserService.authenticate_user(
        db, login_data.phone, login_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone or password",
        )

    access_token = create_jwt_token(subject=str(user["id"]))

    return LoginResponse(access_token=access_token, user=UserResponse(**user))


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse(**current_user)


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    db: Database,
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update current user profile."""
    updated_user = await UserService.update_user(db, current_user["id"], user_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(**updated_user)


@router.get("/wallet/balance", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    db: Database,
    current_user: dict = Depends(get_current_user),
):
    """Get user wallet balance."""
    balance = await TransactionService.get_wallet_balance(db, current_user["id"])
    if balance is None:
        raise HTTPException(status_code=404, detail="User not found")

    return WalletBalanceResponse(user_id=current_user["id"], balance=balance)


@router.post("/wallet/topup")
async def top_up_wallet(
    db: Database,
    topup_data: WalletTopUpRequest,
    current_user: dict = Depends(get_current_user),
):
    """Top up user wallet."""
    result = await TransactionService.top_up_wallet(
        db, current_user["id"], topup_data.amount, topup_data.payment_type
    )
    return {
        "message": "Wallet topped up successfully",
        "new_balance": result["new_balance"],
        "transaction_id": result["transaction"]["id"],
    }


@router.get("/trips", response_model=List[TripResponse])
async def get_user_trips(
    db: Database,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
):
    """Get user trips as passenger."""
    trips = await TripService.get_trips_by_user(
        db, current_user["id"], is_driver=False, skip=skip, limit=limit
    )
    return [TripResponse(**trip) for trip in trips]


@router.post("/trips/estimate", response_model=TripEstimateResponse)
async def estimate_trip(
    db: Database,
    trip_request: TripSearchRequest,
    current_user: dict = Depends(get_current_user_optional),
):
    """Estimate trip cost and details."""
    estimate = await TripService.estimate_trip(
        db,
        trip_request.start_location,
        trip_request.end_location,
        trip_request.trip_type or "urban",
    )
    return TripEstimateResponse(**estimate)


@router.post("/trips", response_model=TripResponse)
async def create_trip(
    db: Database,
    trip_request: TripSearchRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a new trip request."""
    from app.schemas.trip import TripCreate

    trip_data = TripCreate(
        passenger_id=current_user["id"],
        trip_type=trip_request.trip_type or "urban",
        start_location=trip_request.start_location,
        end_location=trip_request.end_location,
    )

    trip = await TripService.create_trip(db, trip_data)
    return TripResponse(**trip)
