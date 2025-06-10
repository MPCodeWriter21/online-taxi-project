"""User service for handling user-related operations."""

# yapf: disable

from typing import List, Optional
from datetime import datetime

import psycopg
from fastapi import HTTPException

from app.schemas.user import (UserCreate, UserUpdate, AdminCreate, DriverCreate,
                              DriverUpdate)
from app.core.security import verify_password, get_password_hash

# yapf: enable


class UserService:
    """Service class for user operations."""

    @staticmethod
    async def create_user(db: psycopg.AsyncConnection, user_data: UserCreate) -> dict:
        """Create a new user."""
        hashed_password = get_password_hash(user_data.password)

        async with db.cursor() as cur:
            # Check if phone already exists
            await cur.execute(
                "SELECT id FROM users WHERE phone = %s OR email = %s",
                (user_data.phone, user_data.email),
            )
            if await cur.fetchone():
                raise HTTPException(
                    status_code=400, detail="Phone or email already registered"
                )

            # Insert new user
            await cur.execute(
                """
                INSERT INTO users (name, phone, email, password_hash, wallet_balance, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, name, phone, email, registration_date, wallet_balance, status, created_at, updated_at
                """,
                (
                    user_data.name,
                    user_data.phone,
                    user_data.email,
                    hashed_password,
                    0,
                    "active",
                ),
            )

            result = await cur.fetchone()
            await db.commit()

            return {
                "id": result[0],
                "name": result[1],
                "phone": result[2],
                "email": result[3],
                "registration_date": result[4],
                "wallet_balance": result[5],
                "status": result[6],
                "created_at": result[7],
                "updated_at": result[8],
            }

    @staticmethod
    async def get_user_by_id(db: psycopg.AsyncConnection,
                             user_id: int) -> Optional[dict]:
        """Get user by ID."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                SELECT id, name, phone, email, registration_date, wallet_balance, status, created_at, updated_at
                FROM users WHERE id = %s AND deleted_at IS NULL
                """,
                (user_id, ),
            )

            result = await cur.fetchone()
            if not result:
                return None

            return {
                "id": result[0],
                "name": result[1],
                "phone": result[2],
                "email": result[3],
                "registration_date": result[4],
                "wallet_balance": result[5],
                "status": result[6],
                "created_at": result[7],
                "updated_at": result[8],
            }

    @staticmethod
    async def get_user_by_phone(db: psycopg.AsyncConnection,
                                phone: str) -> Optional[dict]:
        """Get user by phone number."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                SELECT id, name, phone, email, registration_date, wallet_balance, status,
                       created_at, updated_at, password_hash
                FROM users WHERE phone = %s AND deleted_at IS NULL
                """,
                (phone, ),
            )

            result = await cur.fetchone()
            if not result:
                return None

            return {
                "id": result[0],
                "name": result[1],
                "phone": result[2],
                "email": result[3],
                "registration_date": result[4],
                "wallet_balance": result[5],
                "status": result[6],
                "created_at": result[7],
                "updated_at": result[8],
                "password_hash": result[9],
            }

    @staticmethod
    async def authenticate_user(db: psycopg.AsyncConnection, phone: str,
                                password: str) -> Optional[dict]:
        """Authenticate user with phone and password."""
        user = await UserService.get_user_by_phone(db, phone)
        if not user:
            return None

        if not verify_password(password, user["password_hash"]):
            return None

        # Remove password_hash from response
        del user["password_hash"]
        return user

    @staticmethod
    async def update_user(
        db: psycopg.AsyncConnection, user_id: int, user_data: UserUpdate
    ) -> Optional[dict]:
        """Update user information."""
        update_fields = []
        values = []

        if user_data.name is not None:
            update_fields.append("name = %s")
            values.append(user_data.name)

        if user_data.phone is not None:
            update_fields.append("phone = %s")
            values.append(user_data.phone)

        if user_data.email is not None:
            update_fields.append("email = %s")
            values.append(user_data.email)

        if user_data.status is not None:
            update_fields.append("status = %s")
            values.append(user_data.status)

        if not update_fields:
            return await UserService.get_user_by_id(db, user_id)

        update_fields.append("updated_at = %s")
        values.append(datetime.now())
        values.append(user_id)

        async with db.cursor() as cur:
            await cur.execute(
                f"""
                UPDATE users SET {", ".join(update_fields)}
                WHERE id = %s AND deleted_at IS NULL
                RETURNING id, name, phone, email, registration_date, wallet_balance, status, created_at, updated_at
                """,
                values,
            )

            result = await cur.fetchone()
            await db.commit()

            if not result:
                return None

            return {
                "id": result[0],
                "name": result[1],
                "phone": result[2],
                "email": result[3],
                "registration_date": result[4],
                "wallet_balance": result[5],
                "status": result[6],
                "created_at": result[7],
                "updated_at": result[8],
            }

    @staticmethod
    async def delete_user(db: psycopg.AsyncConnection, user_id: int) -> bool:
        """Soft delete user."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                UPDATE users SET deleted_at = %s, updated_at = %s
                WHERE id = %s AND deleted_at IS NULL
                """,
                (datetime.now(), datetime.now(), user_id),
            )

            await db.commit()
            return cur.rowcount > 0

    @staticmethod
    async def get_users(db: psycopg.AsyncConnection,
                        skip: int = 0,
                        limit: int = 100) -> List[dict]:
        """Get list of users with pagination."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                SELECT id, name, phone, email, registration_date, wallet_balance, status, created_at, updated_at
                FROM users WHERE deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (limit, skip),
            )

            results = await cur.fetchall()
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "phone": row[2],
                    "email": row[3],
                    "registration_date": row[4],
                    "wallet_balance": row[5],
                    "status": row[6],
                    "created_at": row[7],
                    "updated_at": row[8],
                } for row in results
            ]


class DriverService:
    """Service class for driver operations."""

    @staticmethod
    async def create_driver(
        db: psycopg.AsyncConnection, driver_data: DriverCreate
    ) -> dict:
        """Create a new driver."""
        async with db.cursor() as cur:
            # Check if user exists
            await cur.execute(
                "SELECT id FROM users WHERE id = %s", (driver_data.user_id, )
            )
            if not await cur.fetchone():
                raise HTTPException(status_code=404, detail="User not found")

            # Check if driver already exists
            await cur.execute(
                "SELECT user_id FROM drivers WHERE user_id = %s",
                (driver_data.user_id, )
            )
            if await cur.fetchone():
                raise HTTPException(
                    status_code=400, detail="Driver already exists for this user"
                )

            # Insert new driver
            await cur.execute(
                """
                INSERT INTO drivers (user_id, license_number, car_info, approval_status)
                VALUES (%s, %s, %s, %s)
                RETURNING user_id, license_number, car_info, approval_status, created_at, updated_at
                """,
                (
                    driver_data.user_id,
                    driver_data.license_number,
                    driver_data.car_info,
                    "pending",
                ),
            )

            result = await cur.fetchone()
            await db.commit()

            return {
                "user_id": result[0],
                "license_number": result[1],
                "car_info": result[2],
                "approval_status": result[3],
                "created_at": result[4],
                "updated_at": result[5],
            }

    @staticmethod
    async def get_driver_by_user_id(db: psycopg.AsyncConnection,
                                    user_id: int) -> Optional[dict]:
        """Get driver by user ID."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                SELECT d.user_id, d.license_number, d.car_info, d.approval_status, d.created_at, d.updated_at,
                       u.id, u.name, u.phone, u.email, u.registration_date, u.wallet_balance, u.status,
                       u.created_at, u.updated_at
                FROM drivers d
                JOIN users u ON d.user_id = u.id
                WHERE d.user_id = %s AND d.deleted_at IS NULL AND u.deleted_at IS NULL
                """,
                (user_id, ),
            )

            result = await cur.fetchone()
            if not result:
                return None

            return {
                "user_id": result[0],
                "license_number": result[1],
                "car_info": result[2],
                "approval_status": result[3],
                "created_at": result[4],
                "updated_at": result[5],
                "user": {
                    "id": result[6],
                    "name": result[7],
                    "phone": result[8],
                    "email": result[9],
                    "registration_date": result[10],
                    "wallet_balance": result[11],
                    "status": result[12],
                    "created_at": result[13],
                    "updated_at": result[14],
                },
            }

    @staticmethod
    async def update_driver(
        db: psycopg.AsyncConnection, user_id: int, driver_data: DriverUpdate
    ) -> Optional[dict]:
        """Update driver information."""
        update_fields = []
        values = []

        if driver_data.license_number is not None:
            update_fields.append("license_number = %s")
            values.append(driver_data.license_number)

        if driver_data.car_info is not None:
            update_fields.append("car_info = %s")
            values.append(driver_data.car_info)

        if driver_data.approval_status is not None:
            update_fields.append("approval_status = %s")
            values.append(driver_data.approval_status)

        if not update_fields:
            return await DriverService.get_driver_by_user_id(db, user_id)

        update_fields.append("updated_at = %s")
        values.append(datetime.now())
        values.append(user_id)

        async with db.cursor() as cur:
            await cur.execute(
                f"""
                UPDATE drivers SET {", ".join(update_fields)}
                WHERE user_id = %s AND deleted_at IS NULL
                """,
                values,
            )

            await db.commit()

            if cur.rowcount == 0:
                return None

            return await DriverService.get_driver_by_user_id(db, user_id)


class AdminService:
    """Service class for admin operations."""

    @staticmethod
    async def create_admin(
        db: psycopg.AsyncConnection, admin_data: AdminCreate
    ) -> dict:
        """Create a new admin."""
        async with db.cursor() as cur:
            # Check if user exists
            await cur.execute(
                "SELECT id FROM users WHERE id = %s", (admin_data.user_id, )
            )
            if not await cur.fetchone():
                raise HTTPException(status_code=404, detail="User not found")

            # Check if admin already exists
            await cur.execute(
                "SELECT user_id FROM admins WHERE user_id = %s", (admin_data.user_id, )
            )
            if await cur.fetchone():
                raise HTTPException(
                    status_code=400, detail="Admin already exists for this user"
                )

            # Insert new admin
            await cur.execute(
                """
                INSERT INTO admins (user_id, access_level)
                VALUES (%s, %s)
                RETURNING user_id, access_level, created_at, updated_at
                """,
                (admin_data.user_id, admin_data.access_level or "normal"),
            )

            result = await cur.fetchone()
            await db.commit()

            return {
                "user_id": result[0],
                "access_level": result[1],
                "created_at": result[2],
                "updated_at": result[3],
            }

    @staticmethod
    async def get_admin_by_user_id(db: psycopg.AsyncConnection,
                                   user_id: int) -> Optional[dict]:
        """Get admin by user ID."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                SELECT a.user_id, a.access_level, a.created_at, a.updated_at,
                       u.id, u.name, u.phone, u.email, u.registration_date, u.wallet_balance, u.status,
                       u.created_at, u.updated_at
                FROM admins a
                JOIN users u ON a.user_id = u.id
                WHERE a.user_id = %s AND a.deleted_at IS NULL AND u.deleted_at IS NULL
                """,
                (user_id, ),
            )

            result = await cur.fetchone()
            if not result:
                return None

            return {
                "user_id": result[0],
                "access_level": result[1],
                "created_at": result[2],
                "updated_at": result[3],
                "user": {
                    "id": result[4],
                    "name": result[5],
                    "phone": result[6],
                    "email": result[7],
                    "registration_date": result[8],
                    "wallet_balance": result[9],
                    "status": result[10],
                    "created_at": result[11],
                    "updated_at": result[12],
                },
            }
