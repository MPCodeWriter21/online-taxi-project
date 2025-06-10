"""Trip service for handling trip-related operations."""

import math
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

import psycopg
from fastapi import HTTPException

from ..types import TripType, TripStatus
from ..models import Coordinate
from ..schemas.trip import TripCreate, TripUpdate, RouteCreate, TariffCreate


class TripService:
    """Service class for trip operations."""

    @staticmethod
    async def create_trip(db: psycopg.AsyncConnection, trip_data: TripCreate) -> dict:
        """Create a new trip."""
        async with db.cursor() as cur:
            # Check if passenger exists
            await cur.execute(
                "SELECT id FROM users WHERE id = %s", (trip_data.passenger_id, )
            )
            if not await cur.fetchone():
                raise HTTPException(status_code=404, detail="Passenger not found")

            # Insert new trip
            start_location_wkt = None
            end_location_wkt = None

            if trip_data.start_location:
                start_location_wkt = f"POINT({trip_data.start_location.lng} {trip_data.start_location.lat})"

            if trip_data.end_location:
                end_location_wkt = (
                    f"POINT({trip_data.end_location.lng} {trip_data.end_location.lat})"
                )

            await cur.execute(
                """
                INSERT INTO trips (passenger_id, driver_id, route_id, trip_status, trip_type,
                                 discount_code_id, start_location, end_location)
                VALUES (%s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326), ST_GeomFromText(%s, 4326))
                RETURNING id, passenger_id, driver_id, route_id, start_time, end_time, trip_status,
                         trip_type, payment_id, discount_code_id, created_at, updated_at
                """,
                (
                    trip_data.passenger_id,
                    trip_data.driver_id,
                    trip_data.route_id,
                    "pending",
                    trip_data.trip_type,
                    trip_data.discount_code_id,
                    start_location_wkt,
                    end_location_wkt,
                ),
            )

            result = await cur.fetchone()
            await db.commit()

            return {
                "id": result[0],
                "passenger_id": result[1],
                "driver_id": result[2],
                "route_id": result[3],
                "start_time": result[4],
                "end_time": result[5],
                "trip_status": result[6],
                "trip_type": result[7],
                "payment_id": result[8],
                "discount_code_id": result[9],
                "created_at": result[10],
                "updated_at": result[11],
            }

    @staticmethod
    async def get_trip_by_id(db: psycopg.AsyncConnection,
                             trip_id: int) -> Optional[dict]:
        """Get trip by ID."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                SELECT id, passenger_id, driver_id, route_id, start_time, end_time, trip_status,
                       trip_type, payment_id, discount_code_id,
                       ST_X(start_location) as start_lng, ST_Y(start_location) as start_lat,
                       ST_X(end_location) as end_lng, ST_Y(end_location) as end_lat,
                       created_at, updated_at
                FROM trips WHERE id = %s AND deleted_at IS NULL
                """,
                (trip_id, ),
            )

            result = await cur.fetchone()
            if not result:
                return None

            trip = {
                "id": result[0],
                "passenger_id": result[1],
                "driver_id": result[2],
                "route_id": result[3],
                "start_time": result[4],
                "end_time": result[5],
                "trip_status": result[6],
                "trip_type": result[7],
                "payment_id": result[8],
                "discount_code_id": result[9],
                "created_at": result[14],
                "updated_at": result[15],
            }

            # Add coordinates if they exist
            if result[10] is not None and result[11] is not None:
                trip["start_location"] = Coordinate(lng=result[10], lat=result[11])

            if result[12] is not None and result[13] is not None:
                trip["end_location"] = Coordinate(lng=result[12], lat=result[13])

            return trip

    @staticmethod
    async def update_trip(
        db: psycopg.AsyncConnection, trip_id: int, trip_data: TripUpdate
    ) -> Optional[dict]:
        """Update trip information."""
        update_fields = []
        values = []

        if trip_data.driver_id is not None:
            update_fields.append("driver_id = %s")
            values.append(trip_data.driver_id)

        if trip_data.trip_status is not None:
            update_fields.append("trip_status = %s")
            values.append(trip_data.trip_status)

        if trip_data.start_time is not None:
            update_fields.append("start_time = %s")
            values.append(trip_data.start_time)

        if trip_data.end_time is not None:
            update_fields.append("end_time = %s")
            values.append(trip_data.end_time)

        if trip_data.payment_id is not None:
            update_fields.append("payment_id = %s")
            values.append(trip_data.payment_id)

        if not update_fields:
            return await TripService.get_trip_by_id(db, trip_id)

        update_fields.append("updated_at = %s")
        values.append(datetime.now())
        values.append(trip_id)

        async with db.cursor() as cur:
            await cur.execute(
                f"""
                UPDATE trips SET {", ".join(update_fields)}
                WHERE id = %s AND deleted_at IS NULL
                """,
                values,
            )

            await db.commit()

            if cur.rowcount == 0:
                return None

            return await TripService.get_trip_by_id(db, trip_id)

    @staticmethod
    async def get_trips_by_user(
        db: psycopg.AsyncConnection,
        user_id: int,
        is_driver: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[dict]:
        """Get trips by user (passenger or driver)."""
        field = "driver_id" if is_driver else "passenger_id"

        async with db.cursor() as cur:
            await cur.execute(
                f"""
                SELECT id, passenger_id, driver_id, route_id, start_time, end_time, trip_status,
                       trip_type, payment_id, discount_code_id,
                       ST_X(start_location) as start_lng, ST_Y(start_location) as start_lat,
                       ST_X(end_location) as end_lng, ST_Y(end_location) as end_lat,
                       created_at, updated_at
                FROM trips WHERE {field} = %s AND deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, limit, skip),
            )

            results = await cur.fetchall()
            trips = []

            for row in results:
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

            return trips

    @staticmethod
    async def estimate_trip(
        db: psycopg.AsyncConnection,
        start_location: Coordinate,
        end_location: Coordinate,
        trip_type: TripType = "urban",
    ) -> dict:
        """Estimate trip cost and details."""
        # Calculate distance using Haversine formula
        distance_km = TripService._calculate_distance(start_location, end_location)

        async with db.cursor() as cur:
            # Get pricing from tariffs (use a default city for now)
            await cur.execute(
                """
                SELECT price_per_km FROM tariffs
                WHERE trip_type = %s
                ORDER BY created_at DESC LIMIT 1
                """,
                (trip_type, ),
            )

            result = await cur.fetchone()
            price_per_km = result[0] if result else Decimal("10.0")  # Default price

            # Count available drivers (those who are approved and not on a trip)
            await cur.execute(
                """
                SELECT COUNT(*) FROM drivers d
                WHERE d.approval_status = 'approved'
                AND d.deleted_at IS NULL
                AND d.user_id NOT IN (
                    SELECT driver_id FROM trips
                    WHERE trip_status IN ('pending', 'started', 'waiting')
                    AND driver_id IS NOT NULL
                )
                """
            )

            available_drivers = (await cur.fetchone())[0]

        estimated_price = distance_km * price_per_km
        estimated_duration = int(distance_km * 2)  # Rough estimate: 2 minutes per km

        return {
            "estimated_distance_km": distance_km,
            "estimated_price": estimated_price,
            "estimated_duration_minutes": estimated_duration,
            "available_drivers": available_drivers,
        }

    @staticmethod
    def _calculate_distance(coord1: Coordinate, coord2: Coordinate) -> Decimal:
        """Calculate distance between two coordinates using Haversine formula."""
        # Earth radius in kilometers
        R = 6371.0

        # Convert decimal degrees to radians
        lat1_rad = math.radians(coord1.lat)
        lon1_rad = math.radians(coord1.lng)
        lat2_rad = math.radians(coord2.lat)
        lon2_rad = math.radians(coord2.lng)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
            math.sin(dlat / 2)**2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return Decimal(str(round(distance, 2)))

    @staticmethod
    async def assign_driver_to_trip(
        db: psycopg.AsyncConnection, trip_id: int, driver_id: int
    ) -> bool:
        """Assign a driver to a trip."""
        async with db.cursor() as cur:
            # Check if driver is available
            await cur.execute(
                """
                SELECT user_id FROM drivers
                WHERE user_id = %s AND approval_status = 'approved' AND deleted_at IS NULL
                """,
                (driver_id, ),
            )

            if not await cur.fetchone():
                raise HTTPException(status_code=400, detail="Driver not available")

            # Check if driver is already on another active trip
            await cur.execute(
                """
                SELECT id FROM trips
                WHERE driver_id = %s AND trip_status IN ('pending', 'started', 'waiting')
                AND deleted_at IS NULL
                """,
                (driver_id, ),
            )

            if await cur.fetchone():
                raise HTTPException(
                    status_code=400, detail="Driver is already on another trip"
                )

            # Assign driver to trip
            await cur.execute(
                """
                UPDATE trips SET driver_id = %s, updated_at = %s
                WHERE id = %s AND trip_status = 'pending' AND deleted_at IS NULL
                """,
                (driver_id, datetime.now(), trip_id),
            )

            await db.commit()
            return cur.rowcount > 0

    @staticmethod
    async def get_driver_trips(
        db: psycopg.AsyncConnection,
        driver_id: int,
        status: Optional[TripStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[dict]:
        """Get trips for a specific driver."""
        async with db.cursor() as cur:
            conditions = ["driver_id = %s", "deleted_at IS NULL"]
            values = [driver_id]

            if status:
                conditions.append("trip_status = %s")
                values.append(status)

            values.extend([limit, skip])

            await cur.execute(
                f"""
                SELECT id, passenger_id, driver_id, route_id, start_time, end_time,
                       trip_status, trip_type, payment_id, discount_code_id,
                       ST_X(start_location) as start_lng, ST_Y(start_location) as start_lat,
                       ST_X(end_location) as end_lng, ST_Y(end_location) as end_lat,
                       created_at, updated_at
                FROM trips
                WHERE {" AND ".join(conditions)}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                values,
            )

            results = await cur.fetchall()
            trips = []

            for row in results:
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

            return trips

    @staticmethod
    async def get_available_trips(
        db: psycopg.AsyncConnection, skip: int = 0, limit: int = 100
    ) -> List[dict]:
        """Get available trips for drivers to accept."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                SELECT id, passenger_id, driver_id, route_id, start_time, end_time,
                       trip_status, trip_type, payment_id, discount_code_id,
                       ST_X(start_location) as start_lng, ST_Y(start_location) as start_lat,
                       ST_X(end_location) as end_lng, ST_Y(end_location) as end_lat,
                       created_at, updated_at
                FROM trips
                WHERE trip_status = 'pending' AND driver_id IS NULL AND deleted_at IS NULL
                ORDER BY created_at ASC
                LIMIT %s OFFSET %s
                """,
                (limit, skip),
            )

            results = await cur.fetchall()
            trips = []

            for row in results:
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

            return trips

    @staticmethod
    async def accept_trip(db: psycopg.AsyncConnection, trip_id: int,
                          driver_id: int) -> Optional[dict]:
        """Accept a trip request."""
        async with db.cursor() as cur:
            # Check if trip is available
            await cur.execute(
                """
                SELECT id, trip_status, driver_id
                FROM trips
                WHERE id = %s AND deleted_at IS NULL
                """,
                (trip_id, ),
            )

            trip = await cur.fetchone()
            if not trip:
                return None

            if trip[1] != "pending" or trip[2] is not None:
                return None  # Trip not available

            # Update trip with driver
            await cur.execute(
                """
                UPDATE trips
                SET driver_id = %s, trip_status = 'accepted', updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, passenger_id, driver_id, route_id, start_time, end_time,
                         trip_status, trip_type, payment_id, discount_code_id,
                         ST_X(start_location) as start_lng, ST_Y(start_location) as start_lat,
                         ST_X(end_location) as end_lng, ST_Y(end_location) as end_lat,
                         created_at, updated_at
                """,
                (driver_id, trip_id),
            )

            result = await cur.fetchone()
            await db.commit()

            if result:
                trip_data = {
                    "id": result[0],
                    "passenger_id": result[1],
                    "driver_id": result[2],
                    "route_id": result[3],
                    "start_time": result[4],
                    "end_time": result[5],
                    "trip_status": result[6],
                    "trip_type": result[7],
                    "payment_id": result[8],
                    "discount_code_id": result[9],
                    "created_at": result[14],
                    "updated_at": result[15],
                }

                # Add coordinates if they exist
                if result[10] is not None and result[11] is not None:
                    trip_data["start_location"] = Coordinate(
                        lng=result[10], lat=result[11]
                    )

                if result[12] is not None and result[13] is not None:
                    trip_data["end_location"] = Coordinate(
                        lng=result[12], lat=result[13]
                    )

                return trip_data

            return None

    @staticmethod
    async def start_trip(db: psycopg.AsyncConnection, trip_id: int,
                         driver_id: int) -> Optional[dict]:
        """Start an accepted trip."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                UPDATE trips
                SET trip_status = 'in_progress', start_time = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND driver_id = %s AND trip_status = 'accepted'
                RETURNING id, passenger_id, driver_id, route_id, start_time, end_time,
                         trip_status, trip_type, payment_id, discount_code_id,
                         ST_X(start_location) as start_lng, ST_Y(start_location) as start_lat,
                         ST_X(end_location) as end_lng, ST_Y(end_location) as end_lat,
                         created_at, updated_at
                """,
                (trip_id, driver_id),
            )

            result = await cur.fetchone()
            if result:
                await db.commit()

                trip_data = {
                    "id": result[0],
                    "passenger_id": result[1],
                    "driver_id": result[2],
                    "route_id": result[3],
                    "start_time": result[4],
                    "end_time": result[5],
                    "trip_status": result[6],
                    "trip_type": result[7],
                    "payment_id": result[8],
                    "discount_code_id": result[9],
                    "created_at": result[14],
                    "updated_at": result[15],
                }

                # Add coordinates if they exist
                if result[10] is not None and result[11] is not None:
                    trip_data["start_location"] = Coordinate(
                        lng=result[10], lat=result[11]
                    )

                if result[12] is not None and result[13] is not None:
                    trip_data["end_location"] = Coordinate(
                        lng=result[12], lat=result[13]
                    )

                return trip_data

            return None

    @staticmethod
    async def complete_trip(db: psycopg.AsyncConnection, trip_id: int,
                            driver_id: int) -> Optional[dict]:
        """Complete a trip."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                UPDATE trips
                SET trip_status = 'completed', end_time = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND driver_id = %s AND trip_status = 'in_progress'
                RETURNING id, passenger_id, driver_id, route_id, start_time, end_time,
                         trip_status, trip_type, payment_id, discount_code_id,
                         ST_X(start_location) as start_lng, ST_Y(start_location) as start_lat,
                         ST_X(end_location) as end_lng, ST_Y(end_location) as end_lat,
                         created_at, updated_at
                """,
                (trip_id, driver_id),
            )

            result = await cur.fetchone()
            if result:
                await db.commit()

                trip_data = {
                    "id": result[0],
                    "passenger_id": result[1],
                    "driver_id": result[2],
                    "route_id": result[3],
                    "start_time": result[4],
                    "end_time": result[5],
                    "trip_status": result[6],
                    "trip_type": result[7],
                    "payment_id": result[8],
                    "discount_code_id": result[9],
                    "created_at": result[14],
                    "updated_at": result[15],
                }

                # Add coordinates if they exist
                if result[10] is not None and result[11] is not None:
                    trip_data["start_location"] = Coordinate(
                        lng=result[10], lat=result[11]
                    )

                if result[12] is not None and result[13] is not None:
                    trip_data["end_location"] = Coordinate(
                        lng=result[12], lat=result[13]
                    )

                return trip_data

            return None

    @staticmethod
    async def cancel_trip(db: psycopg.AsyncConnection, trip_id: int,
                          driver_id: int) -> Optional[dict]:
        """Cancel a trip."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                UPDATE trips
                SET trip_status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND driver_id = %s
                    AND trip_status IN ('accepted', 'in_progress')
                RETURNING id, passenger_id, driver_id, route_id, start_time, end_time,
                         trip_status, trip_type, payment_id, discount_code_id,
                         ST_X(start_location) as start_lng, ST_Y(start_location) as start_lat,
                         ST_X(end_location) as end_lng, ST_Y(end_location) as end_lat,
                         created_at, updated_at
                """,
                (trip_id, driver_id),
            )

            result = await cur.fetchone()
            if result:
                await db.commit()

                trip_data = {
                    "id": result[0],
                    "passenger_id": result[1],
                    "driver_id": result[2],
                    "route_id": result[3],
                    "start_time": result[4],
                    "end_time": result[5],
                    "trip_status": result[6],
                    "trip_type": result[7],
                    "payment_id": result[8],
                    "discount_code_id": result[9],
                    "created_at": result[14],
                    "updated_at": result[15],
                }

                # Add coordinates if they exist
                if result[10] is not None and result[11] is not None:
                    trip_data["start_location"] = Coordinate(
                        lng=result[10], lat=result[11]
                    )

                if result[12] is not None and result[13] is not None:
                    trip_data["end_location"] = Coordinate(
                        lng=result[12], lat=result[13]
                    )

                return trip_data

            return None


class RouteService:
    """Service class for route operations."""

    @staticmethod
    async def create_route(
        db: psycopg.AsyncConnection, route_data: RouteCreate
    ) -> dict:
        """Create a new route."""
        async with db.cursor() as cur:
            start_location_wkt = None
            end_location_wkt = None

            if route_data.start_location:
                start_location_wkt = f"POINT({route_data.start_location.lng} {route_data.start_location.lat})"

            if route_data.end_location:
                end_location_wkt = f"POINT({route_data.end_location.lng} {route_data.end_location.lat})"

            await cur.execute(
                """
                INSERT INTO routes (start_city_id, end_city_id, start_location, end_location,
                                  is_return, distance_km)
                VALUES (%s, %s, ST_GeomFromText(%s, 4326), ST_GeomFromText(%s, 4326), %s, %s)
                RETURNING id, start_city_id, end_city_id, is_return, distance_km, created_at, updated_at
                """,
                (
                    route_data.start_city_id,
                    route_data.end_city_id,
                    start_location_wkt,
                    end_location_wkt,
                    route_data.is_return,
                    route_data.distance_km,
                ),
            )

            result = await cur.fetchone()
            await db.commit()

            return {
                "id": result[0],
                "start_city_id": result[1],
                "end_city_id": result[2],
                "is_return": result[3],
                "distance_km": result[4],
                "created_at": result[5],
                "updated_at": result[6],
            }


class TariffService:
    """Service class for tariff operations."""

    @staticmethod
    async def create_tariff(
        db: psycopg.AsyncConnection, tariff_data: TariffCreate
    ) -> dict:
        """Create a new tariff."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO tariffs (city_id, trip_type, price_per_km)
                VALUES (%s, %s, %s)
                RETURNING id, city_id, trip_type, price_per_km, created_at, updated_at
                """,
                (tariff_data.city_id, tariff_data.trip_type, tariff_data.price_per_km),
            )

            result = await cur.fetchone()
            await db.commit()

            return {
                "id": result[0],
                "city_id": result[1],
                "trip_type": result[2],
                "price_per_km": result[3],
                "created_at": result[4],
                "updated_at": result[5],
            }

    @staticmethod
    async def get_tariffs(
        db: psycopg.AsyncConnection,
        city_id: Optional[int] = None,
        trip_type: Optional[TripType] = None,
    ) -> List[dict]:
        """Get tariffs with optional filtering."""
        conditions = ["deleted_at IS NULL"]
        values = []

        if city_id is not None:
            conditions.append("city_id = %s")
            values.append(city_id)

        if trip_type is not None:
            conditions.append("trip_type = %s")
            values.append(trip_type)

        async with db.cursor() as cur:
            await cur.execute(
                f"""
                SELECT id, city_id, trip_type, price_per_km, created_at, updated_at
                FROM tariffs WHERE {" AND ".join(conditions)}
                ORDER BY created_at DESC
                """,
                values,
            )

            results = await cur.fetchall()
            return [
                {
                    "id": row[0],
                    "city_id": row[1],
                    "trip_type": row[2],
                    "price_per_km": row[3],
                    "created_at": row[4],
                    "updated_at": row[5],
                } for row in results
            ]
