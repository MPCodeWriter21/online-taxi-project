"""Location management services."""

from typing import Any, Dict, List, Optional

from app.core.db import Database
from app.schemas.location import CityCreate, ProvinceCreate


class ProvinceService:
    """Service for managing provinces."""

    @staticmethod
    async def create_province(db: Database,
                              province_data: ProvinceCreate) -> Dict[str, Any]:
        """Create a new province."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO provinces (name)
                VALUES (%s)
                RETURNING id, name, created_at, updated_at
                """,
                (province_data.name, ),
            )

            result = await cur.fetchone()
            return {
                "id": result[0],
                "name": result[1],
                "created_at": result[2],
                "updated_at": result[3],
            }

    @staticmethod
    async def get_provinces(db: Database,
                            skip: int = 0,
                            limit: int = 100) -> List[Dict[str, Any]]:
        """Get all provinces."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                SELECT id, name, created_at, updated_at
                FROM provinces
                WHERE deleted_at IS NULL
                ORDER BY name
                LIMIT %s OFFSET %s
                """,
                (limit, skip),
            )

            results = await cur.fetchall()
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "created_at": row[2],
                    "updated_at": row[3],
                } for row in results
            ]

    @staticmethod
    async def get_province_by_id(db: Database,
                                 province_id: int) -> Optional[Dict[str, Any]]:
        """Get province by ID."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                SELECT id, name, created_at, updated_at
                FROM provinces
                WHERE id = %s AND deleted_at IS NULL
                """,
                (province_id, ),
            )

            result = await cur.fetchone()
            if result:
                return {
                    "id": result[0],
                    "name": result[1],
                    "created_at": result[2],
                    "updated_at": result[3],
                }
            return None

    @staticmethod
    async def update_province(
        db: Database, province_id: int, province_data: ProvinceCreate
    ) -> Optional[Dict[str, Any]]:
        """Update province."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                UPDATE provinces
                SET name = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND deleted_at IS NULL
                RETURNING id, name, created_at, updated_at
                """,
                (province_data.name, province_id),
            )

            result = await cur.fetchone()
            if result:
                return {
                    "id": result[0],
                    "name": result[1],
                    "created_at": result[2],
                    "updated_at": result[3],
                }
            return None

    @staticmethod
    async def delete_province(db: Database, province_id: int) -> bool:
        """Soft delete province."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                UPDATE provinces
                SET deleted_at = CURRENT_TIMESTAMP
                WHERE id = %s AND deleted_at IS NULL
                """,
                (province_id, ),
            )

            return cur.rowcount > 0


class CityService:
    """Service for managing cities."""

    @staticmethod
    async def create_city(db: Database, city_data: CityCreate) -> Dict[str, Any]:
        """Create a new city."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO cities (name, province_id)
                VALUES (%s, %s)
                RETURNING id, name, province_id, created_at, updated_at
                """,
                (city_data.name, city_data.province_id),
            )

            result = await cur.fetchone()
            return {
                "id": result[0],
                "name": result[1],
                "province_id": result[2],
                "created_at": result[3],
                "updated_at": result[4],
            }

    @staticmethod
    async def get_cities(
        db: Database,
        province_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get cities with optional province filtering."""
        conditions = ["c.deleted_at IS NULL"]
        values = []

        if province_id:
            conditions.append("c.province_id = %s")
            values.append(province_id)

        values.extend([limit, skip])

        async with db.cursor() as cur:
            await cur.execute(
                f"""
                SELECT c.id, c.name, c.province_id, c.created_at, c.updated_at,
                       p.name as province_name
                FROM cities c
                LEFT JOIN provinces p ON c.province_id = p.id
                WHERE {" AND ".join(conditions)}
                ORDER BY c.name
                LIMIT %s OFFSET %s
                """,
                values,
            )

            results = await cur.fetchall()
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "province_id": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                    "province_name": row[5],
                } for row in results
            ]

    @staticmethod
    async def get_city_by_id(db: Database, city_id: int) -> Optional[Dict[str, Any]]:
        """Get city by ID."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                SELECT c.id, c.name, c.province_id, c.created_at, c.updated_at,
                       p.name as province_name
                FROM cities c
                LEFT JOIN provinces p ON c.province_id = p.id
                WHERE c.id = %s AND c.deleted_at IS NULL
                """,
                (city_id, ),
            )

            result = await cur.fetchone()
            if result:
                return {
                    "id": result[0],
                    "name": result[1],
                    "province_id": result[2],
                    "created_at": result[3],
                    "updated_at": result[4],
                    "province_name": result[5],
                }
            return None

    @staticmethod
    async def update_city(db: Database, city_id: int,
                          city_data: CityCreate) -> Optional[Dict[str, Any]]:
        """Update city."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                UPDATE cities
                SET name = %s, province_id = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND deleted_at IS NULL
                RETURNING id, name, province_id, created_at, updated_at
                """,
                (city_data.name, city_data.province_id, city_id),
            )

            result = await cur.fetchone()
            if result:
                return {
                    "id": result[0],
                    "name": result[1],
                    "province_id": result[2],
                    "created_at": result[3],
                    "updated_at": result[4],
                }
            return None

    @staticmethod
    async def delete_city(db: Database, city_id: int) -> bool:
        """Soft delete city."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                UPDATE cities
                SET deleted_at = CURRENT_TIMESTAMP
                WHERE id = %s AND deleted_at IS NULL
                """,
                (city_id, ),
            )

            return cur.rowcount > 0
