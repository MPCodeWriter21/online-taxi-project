"""Driver API endpoints."""

from typing import List, Optional

from fastapi import Query, Depends, APIRouter, HTTPException

from app.types import TripType, TripStatus
from app.core.db import Database
from app.dependencies import get_current_driver
from app.schemas.trip import TripResponse, TariffResponse
from app.schemas.user import DriverUpdate, DriverResponse
from app.services.trip_service import TripService, TariffService
from app.services.user_service import DriverService

router = APIRouter(tags=["driver-api"], prefix="/api")


# Driver Profile Management
@router.get("/profile", response_model=DriverResponse)
async def get_driver_profile(
    db: Database, current_driver: dict = Depends(get_current_driver)
):
    """Get driver profile."""
    driver = await DriverService.get_driver_by_user_id(db, current_driver["id"])
    if not driver:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    return DriverResponse(**driver)


@router.put("/profile", response_model=DriverResponse)
async def update_driver_profile(
    db: Database,
    driver_data: DriverUpdate,
    current_driver: dict = Depends(get_current_driver),
):
    """Update driver profile."""
    updated_driver = await DriverService.update_driver(
        db, current_driver["id"], driver_data
    )
    if not updated_driver:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    return DriverResponse(**updated_driver)


# Trip Management
@router.get("/trips", response_model=List[TripResponse])
async def get_driver_trips(
    db: Database,
    status: Optional[TripStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_driver: dict = Depends(get_current_driver),
):
    """Get driver's trips."""
    trips = await TripService.get_driver_trips(
        db, current_driver["id"], status=status, skip=skip, limit=limit
    )
    return [TripResponse(**trip) for trip in trips]


@router.get("/trips/available", response_model=List[TripResponse])
async def get_available_trips(
    db: Database,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_driver: dict = Depends(get_current_driver),
):
    """Get available trips for driver to accept."""
    trips = await TripService.get_available_trips(db, skip=skip, limit=limit)
    return [TripResponse(**trip) for trip in trips]


@router.post("/trips/{trip_id}/accept", response_model=TripResponse)
async def accept_trip(
    db: Database,
    trip_id: int,
    current_driver: dict = Depends(get_current_driver),
):
    """Accept a trip request."""
    trip = await TripService.accept_trip(db, trip_id, current_driver["id"])
    if not trip:
        raise HTTPException(
            status_code=404, detail="Trip not found or already accepted"
        )

    return TripResponse(**trip)


@router.post("/trips/{trip_id}/start", response_model=TripResponse)
async def start_trip(
    db: Database,
    trip_id: int,
    current_driver: dict = Depends(get_current_driver),
):
    """Start an accepted trip."""
    trip = await TripService.start_trip(db, trip_id, current_driver["id"])
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found or not authorized")

    return TripResponse(**trip)


@router.post("/trips/{trip_id}/complete", response_model=TripResponse)
async def complete_trip(
    db: Database,
    trip_id: int,
    current_driver: dict = Depends(get_current_driver),
):
    """Complete a trip."""
    trip = await TripService.complete_trip(db, trip_id, current_driver["id"])
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found or not authorized")

    return TripResponse(**trip)


@router.post("/trips/{trip_id}/cancel", response_model=TripResponse)
async def cancel_trip(
    db: Database,
    trip_id: int,
    current_driver: dict = Depends(get_current_driver),
):
    """Cancel a trip."""
    trip = await TripService.cancel_trip(db, trip_id, current_driver["id"])
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found or not authorized")

    return TripResponse(**trip)


# Route and Tariff Information
@router.get("/tariffs", response_model=List[TariffResponse])
async def get_tariffs(
    db: Database,
    city_id: Optional[int] = Query(None),
    trip_type: Optional[TripType] = Query(None),
    current_driver: dict = Depends(get_current_driver),
):
    """Get available tariffs."""
    tariffs = await TariffService.get_tariffs(db, city_id=city_id, trip_type=trip_type)
    return [TariffResponse(**tariff) for tariff in tariffs]


# Driver Analytics
@router.get("/analytics/earnings")
async def get_driver_earnings(
    db: Database,
    days: int = Query(30, ge=1, le=365),
    current_driver: dict = Depends(get_current_driver),
):
    """Get driver earnings analytics."""
    async with db.cursor() as cur:
        # Total earnings in the period
        await cur.execute(
            """
            SELECT COALESCE(SUM(p.amount), 0) as total_earnings,
                   COUNT(t.id) as total_trips
            FROM trips t
            JOIN payments p ON t.payment_id = p.id
            WHERE t.driver_id = %s
                AND t.trip_status = 'completed'
                AND t.created_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                AND t.deleted_at IS NULL
            """,
            (current_driver["id"], days),
        )

        result = await cur.fetchone()
        total_earnings = float(result[0]) if result[0] else 0.0
        total_trips = result[1] if result[1] else 0

        # Daily earnings breakdown
        await cur.execute(
            """
            SELECT DATE(t.created_at) as date,
                   COALESCE(SUM(p.amount), 0) as daily_earnings,
                   COUNT(t.id) as daily_trips
            FROM trips t
            JOIN payments p ON t.payment_id = p.id
            WHERE t.driver_id = %s
                AND t.trip_status = 'completed'
                AND t.created_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                AND t.deleted_at IS NULL
            GROUP BY DATE(t.created_at)
            ORDER BY date DESC
            """,
            (current_driver["id"], days),
        )

        daily_breakdown = []
        for row in await cur.fetchall():
            daily_breakdown.append(
                {
                    "date": row[0].isoformat(),
                    "earnings": float(row[1]),
                    "trips": row[2]
                }
            )

        return {
            "total_earnings": total_earnings,
            "total_trips": total_trips,
            "average_per_trip":
            (total_earnings / total_trips if total_trips > 0 else 0.0),
            "daily_breakdown": daily_breakdown,
        }
