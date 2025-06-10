"""Discount code management services."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from app.core.db import Database
from app.schemas.discount import DiscountCodeCreate, DiscountCodeUpdate


class DiscountService:
    """Service for managing discount codes."""

    @staticmethod
    async def create_discount_code(db: Database,
                                   discount_data: DiscountCodeCreate) -> Dict[str, Any]:
        """Create a new discount code."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO discount_codes (
                    code, discount_type, discount_value, min_trip_amount,
                    max_discount_amount, usage_limit, valid_from, valid_until,
                    is_active, created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, code, discount_type, discount_value, min_trip_amount,
                         max_discount_amount, usage_limit, usage_count, valid_from,
                         valid_until, is_active, created_by, created_at, updated_at
                """,
                (
                    discount_data.code,
                    discount_data.discount_type,
                    discount_data.discount_value,
                    discount_data.min_trip_amount,
                    discount_data.max_discount_amount,
                    discount_data.usage_limit,
                    discount_data.valid_from,
                    discount_data.valid_until,
                    discount_data.is_active,
                    discount_data.created_by,
                ),
            )

            result = await cur.fetchone()
            return {
                "id": result[0],
                "code": result[1],
                "discount_type": result[2],
                "discount_value": result[3],
                "min_trip_amount": result[4],
                "max_discount_amount": result[5],
                "usage_limit": result[6],
                "usage_count": result[7],
                "valid_from": result[8],
                "valid_until": result[9],
                "is_active": result[10],
                "created_by": result[11],
                "created_at": result[12],
                "updated_at": result[13],
            }

    @staticmethod
    async def get_discount_codes(
        db: Database,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get discount codes with optional filtering."""
        conditions = ["deleted_at IS NULL"]
        values = []

        if is_active is not None:
            conditions.append("is_active = %s")
            values.append(is_active)

        values.extend([limit, skip])

        async with db.cursor() as cur:
            await cur.execute(
                f"""
                SELECT id, code, discount_type, discount_value, min_trip_amount,
                       max_discount_amount, usage_limit, usage_count, valid_from,
                       valid_until, is_active, created_by, created_at, updated_at
                FROM discount_codes
                WHERE {" AND ".join(conditions)}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                values,
            )

            results = await cur.fetchall()
            return [
                {
                    "id": row[0],
                    "code": row[1],
                    "discount_type": row[2],
                    "discount_value": row[3],
                    "min_trip_amount": row[4],
                    "max_discount_amount": row[5],
                    "usage_limit": row[6],
                    "usage_count": row[7],
                    "valid_from": row[8],
                    "valid_until": row[9],
                    "is_active": row[10],
                    "created_by": row[11],
                    "created_at": row[12],
                    "updated_at": row[13],
                } for row in results
            ]

    @staticmethod
    async def get_discount_code_by_id(db: Database,
                                      discount_id: int) -> Optional[Dict[str, Any]]:
        """Get discount code by ID."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                SELECT id, code, discount_type, discount_value, min_trip_amount,
                       max_discount_amount, usage_limit, usage_count, valid_from,
                       valid_until, is_active, created_by, created_at, updated_at
                FROM discount_codes
                WHERE id = %s AND deleted_at IS NULL
                """,
                (discount_id, ),
            )

            result = await cur.fetchone()
            if result:
                return {
                    "id": result[0],
                    "code": result[1],
                    "discount_type": result[2],
                    "discount_value": result[3],
                    "min_trip_amount": result[4],
                    "max_discount_amount": result[5],
                    "usage_limit": result[6],
                    "usage_count": result[7],
                    "valid_from": result[8],
                    "valid_until": result[9],
                    "is_active": result[10],
                    "created_by": result[11],
                    "created_at": result[12],
                    "updated_at": result[13],
                }
            return None

    @staticmethod
    async def get_discount_code_by_code(db: Database,
                                        code: str) -> Optional[Dict[str, Any]]:
        """Get discount code by code string."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                SELECT id, code, discount_type, discount_value, min_trip_amount,
                       max_discount_amount, usage_limit, usage_count, valid_from,
                       valid_until, is_active, created_by, created_at, updated_at
                FROM discount_codes
                WHERE code = %s AND deleted_at IS NULL
                """,
                (code, ),
            )

            result = await cur.fetchone()
            if result:
                return {
                    "id": result[0],
                    "code": result[1],
                    "discount_type": result[2],
                    "discount_value": result[3],
                    "min_trip_amount": result[4],
                    "max_discount_amount": result[5],
                    "usage_limit": result[6],
                    "usage_count": result[7],
                    "valid_from": result[8],
                    "valid_until": result[9],
                    "is_active": result[10],
                    "created_by": result[11],
                    "created_at": result[12],
                    "updated_at": result[13],
                }
            return None

    @staticmethod
    async def update_discount_code(
        db: Database, discount_id: int, discount_data: DiscountCodeUpdate
    ) -> Optional[Dict[str, Any]]:
        """Update discount code."""
        # Build dynamic update query
        update_fields = []
        values = []

        for field, value in discount_data.model_dump(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = %s")
                values.append(value)

        if not update_fields:
            return await DiscountService.get_discount_code_by_id(db, discount_id)

        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(discount_id)

        async with db.cursor() as cur:
            await cur.execute(
                f"""
                UPDATE discount_codes
                SET {", ".join(update_fields)}
                WHERE id = %s AND deleted_at IS NULL
                RETURNING id, code, discount_type, discount_value, min_trip_amount,
                         max_discount_amount, usage_limit, usage_count, valid_from,
                         valid_until, is_active, created_by, created_at, updated_at
                """,
                values,
            )

            result = await cur.fetchone()
            if result:
                return {
                    "id": result[0],
                    "code": result[1],
                    "discount_type": result[2],
                    "discount_value": result[3],
                    "min_trip_amount": result[4],
                    "max_discount_amount": result[5],
                    "usage_limit": result[6],
                    "usage_count": result[7],
                    "valid_from": result[8],
                    "valid_until": result[9],
                    "is_active": result[10],
                    "created_by": result[11],
                    "created_at": result[12],
                    "updated_at": result[13],
                }
            return None

    @staticmethod
    async def delete_discount_code(db: Database, discount_id: int) -> bool:
        """Soft delete discount code."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                UPDATE discount_codes
                SET deleted_at = CURRENT_TIMESTAMP
                WHERE id = %s AND deleted_at IS NULL
                """,
                (discount_id, ),
            )

            return cur.rowcount > 0

    @staticmethod
    async def validate_discount_code(
        db: Database, code: str, trip_amount: float, user_id: int
    ) -> Dict[str, Any]:
        """Validate discount code for a trip."""
        discount = await DiscountService.get_discount_code_by_code(db, code)

        if not discount:
            return {"valid": False, "error": "Discount code not found"}

        # Check if code is active
        if not discount["is_active"]:
            return {"valid": False, "error": "Discount code is not active"}

        # Check date validity
        now = datetime.now()
        if discount["valid_from"] and now < discount["valid_from"]:
            return {"valid": False, "error": "Discount code is not yet valid"}

        if discount["valid_until"] and now > discount["valid_until"]:
            return {"valid": False, "error": "Discount code has expired"}

        # Check minimum trip amount
        if discount["min_trip_amount"] and trip_amount < discount["min_trip_amount"]:
            return {
                "valid": False,
                "error": f"Minimum trip amount is {discount['min_trip_amount']}",
            }

        # Check usage limit
        if (discount["usage_limit"]
                and discount["usage_count"] >= discount["usage_limit"]):
            return {"valid": False, "error": "Discount code usage limit reached"}

        # Check if user already used this code
        async with db.cursor() as cur:
            await cur.execute(
                """
                SELECT COUNT(*) FROM trips
                WHERE passenger_id = %s AND discount_code_id = %s AND deleted_at IS NULL
                """,
                (user_id, discount["id"]),
            )

            usage_count = (await cur.fetchone())[0]
            if usage_count > 0:
                return {
                    "valid": False,
                    "error": "You have already used this discount code",
                }

        # Calculate discount amount
        discount_amount = 0
        if discount["discount_type"] == "percentage":
            discount_amount = trip_amount * (discount["discount_value"] / 100)
        elif discount["discount_type"] == "fixed":
            discount_amount = discount["discount_value"]

        # Apply maximum discount limit
        if discount["max_discount_amount"]:
            discount_amount = min(discount_amount, discount["max_discount_amount"])

        return {
            "valid": True,
            "discount_id": discount["id"],
            "discount_amount": discount_amount,
            "final_amount": max(0, trip_amount - discount_amount),
        }

    @staticmethod
    async def increment_usage_count(db: Database, discount_id: int) -> bool:
        """Increment usage count for a discount code."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                UPDATE discount_codes
                SET usage_count = usage_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND deleted_at IS NULL
                """,
                (discount_id, ),
            )

            return cur.rowcount > 0
