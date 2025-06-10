"""Admin API endpoints."""

# yapf: disable

from typing import List, Optional

from fastapi import Query, Depends, APIRouter, HTTPException

from app.types import TripType, DriverApprovalStatus
from app.core.db import Database
from app.dependencies import get_current_admin, get_current_superuser
from app.schemas.trip import TariffCreate, TripResponse, TariffResponse
from app.schemas.user import (UserUpdate, AdminCreate, DriverUpdate, UserResponse,
                              AdminResponse, DriverResponse)
from app.schemas.location import (CityCreate, CityResponse, ProvinceCreate,
                                  ProvinceResponse)
from app.services.trip_service import TariffService
from app.services.user_service import UserService, AdminService, DriverService
from app.services.location_service import CityService, ProvinceService

# yapf: enable

router = APIRouter(tags=["admin-api"], prefix="/api")


# User Management
@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    db: Database,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: dict = Depends(get_current_admin),
):
    """Get all users (admin only)."""
    users = await UserService.get_users(db, skip=skip, limit=limit)
    return [UserResponse(**user) for user in users]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    db: Database,
    user_id: int,
    current_admin: dict = Depends(get_current_admin),
):
    """Get user by ID (admin only)."""
    user = await UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(**user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user_by_admin(
    db: Database,
    user_id: int,
    user_data: UserUpdate,
    current_admin: dict = Depends(get_current_admin),
):
    """Update user by admin."""
    updated_user = await UserService.update_user(db, user_id, user_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(**updated_user)


@router.delete("/users/{user_id}")
async def delete_user(
    db: Database,
    user_id: int,
    current_admin: dict = Depends(get_current_superuser),
):
    """Delete user (superuser only)."""
    success = await UserService.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}


# Driver Management
@router.get("/drivers", response_model=List[DriverResponse])
async def get_all_drivers(
    db: Database,
    approval_status: Optional[DriverApprovalStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: dict = Depends(get_current_admin),
):
    """Get all drivers with optional filtering."""
    async with db.cursor() as cur:
        conditions = ["d.deleted_at IS NULL", "u.deleted_at IS NULL"]
        values = []

        if approval_status:
            conditions.append("d.approval_status = %s")
            values.append(approval_status)

        values.extend([limit, skip])

        await cur.execute(
            f"""
            SELECT d.user_id, d.license_number, d.car_info, d.approval_status,
                   d.created_at, d.updated_at,
                   u.id, u.name, u.phone, u.email, u.registration_date,
                   u.wallet_balance, u.status, u.created_at, u.updated_at
            FROM drivers d
            JOIN users u ON d.user_id = u.id
            WHERE {" AND ".join(conditions)}
            ORDER BY d.created_at DESC
            LIMIT %s OFFSET %s
            """,
            values,
        )

        results = await cur.fetchall()
        drivers = []

        for row in results:
            driver = {
                "user_id": row[0],
                "license_number": row[1],
                "car_info": row[2],
                "approval_status": row[3],
                "created_at": row[4],
                "updated_at": row[5],
                "user": {
                    "id": row[6],
                    "name": row[7],
                    "phone": row[8],
                    "email": row[9],
                    "registration_date": row[10],
                    "wallet_balance": row[11],
                    "status": row[12],
                    "created_at": row[13],
                    "updated_at": row[14],
                },
            }
            drivers.append(driver)

        return [DriverResponse(**driver) for driver in drivers]


@router.put("/drivers/{user_id}/approval", response_model=DriverResponse)
async def update_driver_approval(
    db: Database,
    user_id: int,
    approval_data: DriverUpdate,
    current_admin: dict = Depends(get_current_admin),
):
    """Update driver approval status."""
    updated_driver = await DriverService.update_driver(db, user_id, approval_data)
    if not updated_driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    return DriverResponse(**updated_driver)


# Trip Management
@router.get("/trips", response_model=List[TripResponse])
async def get_all_trips(
    db: Database,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: dict = Depends(get_current_admin),
):
    """Get all trips (admin only)."""
    async with db.cursor() as cur:
        await cur.execute(
            """
            SELECT id, passenger_id, driver_id, route_id, start_time, end_time,
                   trip_status, trip_type, payment_id, discount_code_id,
                   ST_X(start_location) as start_lng, ST_Y(start_location) as start_lat,
                   ST_X(end_location) as end_lng, ST_Y(end_location) as end_lat,
                   created_at, updated_at
            FROM trips WHERE deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (limit, skip),
        )

        results = await cur.fetchall()
        trips = []

        for row in results:
            from ...models import Coordinate

            trip = {
                "id": row[0],
                "passenger_id": row[1],
                "driver_id": row[2],
                "route_id": row[3],
                "start_time": row[4],
                "end_time": row[5],
                "trip_status": row[6],
                "trip_type": row[7],
                "payment_id": row[8],
                "discount_code_id": row[9],
                "created_at": row[14],
                "updated_at": row[15],
            }

            # Add coordinates if they exist
            if row[10] is not None and row[11] is not None:
                trip["start_location"] = Coordinate(lng=row[10], lat=row[11])

            if row[12] is not None and row[13] is not None:
                trip["end_location"] = Coordinate(lng=row[12], lat=row[13])

            trips.append(trip)

        return [TripResponse(**trip) for trip in trips]


# Tariff Management
@router.post("/tariffs", response_model=TariffResponse)
async def create_tariff(
    db: Database,
    tariff_data: TariffCreate,
    current_admin: dict = Depends(get_current_admin),
):
    """Create a new tariff."""
    tariff = await TariffService.create_tariff(db, tariff_data)
    return TariffResponse(**tariff)


@router.get("/tariffs", response_model=List[TariffResponse])
async def get_tariffs(
    db: Database,
    city_id: Optional[int] = Query(None),
    trip_type: Optional[TripType] = Query(None),
    current_admin: dict = Depends(get_current_admin),
):
    """Get tariffs with optional filtering."""
    tariffs = await TariffService.get_tariffs(db, city_id=city_id, trip_type=trip_type)
    return [TariffResponse(**tariff) for tariff in tariffs]


# Admin Management (Superuser only)
@router.post("/admins", response_model=AdminResponse)
async def create_admin(
    db: Database,
    admin_data: AdminCreate,
    current_admin: dict = Depends(get_current_superuser),
):
    """Create a new admin (superuser only)."""
    admin = await AdminService.create_admin(db, admin_data)

    # Get full admin info with user details
    full_admin = await AdminService.get_admin_by_user_id(db, admin["user_id"])
    return AdminResponse(**full_admin)


# Analytics and Reports
@router.get("/analytics/dashboard")
async def get_dashboard_analytics(
    db: Database, current_admin: dict = Depends(get_current_admin)
):
    """Get dashboard analytics."""
    async with db.cursor() as cur:
        # Total users
        await cur.execute("SELECT COUNT(*) FROM users WHERE deleted_at IS NULL")
        total_users = (await cur.fetchone())[0]

        # Total drivers
        await cur.execute("SELECT COUNT(*) FROM drivers WHERE deleted_at IS NULL")
        total_drivers = (await cur.fetchone())[0]
        # Active drivers
        await cur.execute(
            """SELECT COUNT(*) FROM drivers
               WHERE approval_status = 'approved' AND deleted_at IS NULL"""
        )
        active_drivers = (await cur.fetchone())[0]

        # Total trips
        await cur.execute("SELECT COUNT(*) FROM trips WHERE deleted_at IS NULL")
        total_trips = (await cur.fetchone())[0]
        # Completed trips
        await cur.execute(
            """SELECT COUNT(*) FROM trips
               WHERE trip_status = 'completed' AND deleted_at IS NULL"""
        )
        completed_trips = (await cur.fetchone())[0]
        # Pending trips
        await cur.execute(
            """SELECT COUNT(*) FROM trips
               WHERE trip_status = 'pending' AND deleted_at IS NULL"""
        )
        pending_trips = (await cur.fetchone())[0]

        # Revenue (completed payments)
        await cur.execute(
            """
            SELECT COALESCE(SUM(amount), 0) FROM payments
            WHERE status = 'completed' AND deleted_at IS NULL
            """
        )
        total_revenue = (await cur.fetchone())[0]

        return {
            "users": {
                "total": total_users,
                "drivers": total_drivers,
                "active_drivers": active_drivers,
            },
            "trips": {
                "total": total_trips,
                "completed": completed_trips,
                "pending": pending_trips,
            },
            "revenue": {
                "total": float(total_revenue)
            },
        }


# Location Management
@router.post("/provinces", response_model=ProvinceResponse)
async def create_province(
    db: Database,
    province_data: ProvinceCreate,
    current_admin: dict = Depends(get_current_admin),
):
    """Create a new province."""
    province = await ProvinceService.create_province(db, province_data)
    return ProvinceResponse(**province)


@router.get("/provinces", response_model=List[ProvinceResponse])
async def get_provinces(
    db: Database,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: dict = Depends(get_current_admin),
):
    """Get all provinces."""
    provinces = await ProvinceService.get_provinces(db, skip=skip, limit=limit)
    return [ProvinceResponse(**province) for province in provinces]


@router.get("/provinces/{province_id}", response_model=ProvinceResponse)
async def get_province_by_id(
    db: Database,
    province_id: int,
    current_admin: dict = Depends(get_current_admin),
):
    """Get province by ID."""
    province = await ProvinceService.get_province_by_id(db, province_id)
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    return ProvinceResponse(**province)


@router.put("/provinces/{province_id}", response_model=ProvinceResponse)
async def update_province(
    db: Database,
    province_id: int,
    province_data: ProvinceCreate,
    current_admin: dict = Depends(get_current_admin),
):
    """Update province."""
    updated_province = await ProvinceService.update_province(
        db, province_id, province_data
    )
    if not updated_province:
        raise HTTPException(status_code=404, detail="Province not found")
    return ProvinceResponse(**updated_province)


@router.delete("/provinces/{province_id}")
async def delete_province(
    db: Database,
    province_id: int,
    current_admin: dict = Depends(get_current_superuser),
):
    """Delete province (superuser only)."""
    success = await ProvinceService.delete_province(db, province_id)
    if not success:
        raise HTTPException(status_code=404, detail="Province not found")
    return {"message": "Province deleted successfully"}


@router.post("/cities", response_model=CityResponse)
async def create_city(
    db: Database,
    city_data: CityCreate,
    current_admin: dict = Depends(get_current_admin),
):
    """Create a new city."""
    city = await CityService.create_city(db, city_data)
    return CityResponse(**city)


@router.get("/cities", response_model=List[CityResponse])
async def get_cities(
    db: Database,
    province_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: dict = Depends(get_current_admin),
):
    """Get cities with optional province filtering."""
    cities = await CityService.get_cities(
        db, province_id=province_id, skip=skip, limit=limit
    )
    return [CityResponse(**city) for city in cities]


@router.get("/cities/{city_id}", response_model=CityResponse)
async def get_city_by_id(
    db: Database,
    city_id: int,
    current_admin: dict = Depends(get_current_admin),
):
    """Get city by ID."""
    city = await CityService.get_city_by_id(db, city_id)
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    return CityResponse(**city)


@router.put("/cities/{city_id}", response_model=CityResponse)
async def update_city(
    db: Database,
    city_id: int,
    city_data: CityCreate,
    current_admin: dict = Depends(get_current_admin),
):
    """Update city."""
    updated_city = await CityService.update_city(db, city_id, city_data)
    if not updated_city:
        raise HTTPException(status_code=404, detail="City not found")
    return CityResponse(**updated_city)


@router.delete("/cities/{city_id}")
async def delete_city(
    db: Database,
    city_id: int,
    current_admin: dict = Depends(get_current_superuser),
):
    """Delete city (superuser only)."""
    success = await CityService.delete_city(db, city_id)
    if not success:
        raise HTTPException(status_code=404, detail="City not found")
    return {"message": "City deleted successfully"}


# Discount Management
@router.post("/discounts", response_model=dict)
async def create_discount(
    db: Database,
    discount_data: dict,
    current_admin: dict = Depends(get_current_admin),
):
    """Create a new discount code."""
    from app.schemas.discount import DiscountCreate
    from app.services.discount_service import DiscountService

    discount_create = DiscountCreate(**discount_data)
    discount = await DiscountService.create_discount(db, discount_create)
    return discount


@router.get("/discounts")
async def get_discounts(
    db: Database,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: dict = Depends(get_current_admin),
):
    """Get all discount codes."""
    from app.services.discount_service import DiscountService

    discounts = await DiscountService.get_discounts(db, skip=skip, limit=limit)
    return discounts
