"""Payment service for handling payment-related operations."""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime

import psycopg
from fastapi import HTTPException

from ..types import PaymentStatus
from ..schemas.payment import PaymentCreate, TransactionCreate


class PaymentService:
    """Service class for payment operations."""

    @staticmethod
    async def create_payment(
        db: psycopg.AsyncConnection, payment_data: PaymentCreate
    ) -> dict:
        """Create a new payment."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO payments (amount, payment_type, status)
                VALUES (%s, %s, %s)
                RETURNING id, amount, payment_type, payment_date, status, created_at, updated_at
                """,
                (payment_data.amount, payment_data.payment_type, "pending"),
            )

            result = await cur.fetchone()
            await db.commit()

            return {
                "id": result[0],
                "amount": result[1],
                "payment_type": result[2],
                "payment_date": result[3],
                "status": result[4],
                "created_at": result[5],
                "updated_at": result[6],
            }

    @staticmethod
    async def update_payment_status(
        db: psycopg.AsyncConnection, payment_id: int, status: PaymentStatus
    ) -> Optional[dict]:
        """Update payment status."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                UPDATE payments SET status = %s, updated_at = %s
                WHERE id = %s AND deleted_at IS NULL
                RETURNING id, amount, payment_type, payment_date, status, created_at, updated_at
                """,
                (status, datetime.now(), payment_id),
            )

            result = await cur.fetchone()
            await db.commit()

            if not result:
                return None

            return {
                "id": result[0],
                "amount": result[1],
                "payment_type": result[2],
                "payment_date": result[3],
                "status": result[4],
                "created_at": result[5],
                "updated_at": result[6],
            }

    @staticmethod
    async def get_payment_by_id(db: psycopg.AsyncConnection,
                                payment_id: int) -> Optional[dict]:
        """Get payment by ID."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                SELECT id, amount, payment_type, payment_date, status, created_at, updated_at
                FROM payments WHERE id = %s AND deleted_at IS NULL
                """,
                (payment_id, ),
            )

            result = await cur.fetchone()
            if not result:
                return None

            return {
                "id": result[0],
                "amount": result[1],
                "payment_type": result[2],
                "payment_date": result[3],
                "status": result[4],
                "created_at": result[5],
                "updated_at": result[6],
            }


class TransactionService:
    """Service class for transaction and wallet operations."""

    @staticmethod
    async def create_transaction(
        db: psycopg.AsyncConnection, transaction_data: TransactionCreate
    ) -> dict:
        """Create a new transaction and update user wallet."""
        async with db.cursor() as cur:
            # Start transaction
            await cur.execute("BEGIN")

            try:
                # Check if user exists
                await cur.execute(
                    "SELECT wallet_balance FROM users WHERE id = %s",
                    (transaction_data.user_id, ),
                )
                result = await cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="User not found")

                current_balance = result[0]

                # Check if user has sufficient balance for withdrawals
                if transaction_data.type in [
                        "withdraw",
                        "trip_payment",
                ] and current_balance < abs(transaction_data.amount):
                    raise HTTPException(
                        status_code=400, detail="Insufficient wallet balance"
                    )

                # Create transaction record
                await cur.execute(
                    """
                    INSERT INTO transactions (user_id, amount, type, payment_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, user_id, amount, type, date, payment_id, created_at, updated_at
                    """,
                    (
                        transaction_data.user_id,
                        transaction_data.amount,
                        transaction_data.type,
                        transaction_data.payment_id,
                    ),
                )

                transaction_result = await cur.fetchone()

                # Update user wallet balance
                new_balance = current_balance + transaction_data.amount
                await cur.execute(
                    """
                    UPDATE users SET wallet_balance = %s, updated_at = %s
                    WHERE id = %s
                    """,
                    (new_balance, datetime.now(), transaction_data.user_id),
                )

                await cur.execute("COMMIT")

                return {
                    "id": transaction_result[0],
                    "user_id": transaction_result[1],
                    "amount": transaction_result[2],
                    "type": transaction_result[3],
                    "date": transaction_result[4],
                    "payment_id": transaction_result[5],
                    "created_at": transaction_result[6],
                    "updated_at": transaction_result[7],
                }

            except Exception as e:
                await cur.execute("ROLLBACK")
                raise e

    @staticmethod
    async def get_user_transactions(
        db: psycopg.AsyncConnection,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[dict]:
        """Get user transactions with pagination."""
        async with db.cursor() as cur:
            await cur.execute(
                """
                SELECT id, user_id, amount, type, date, payment_id, created_at, updated_at
                FROM transactions WHERE user_id = %s AND deleted_at IS NULL
                ORDER BY date DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, limit, skip),
            )

            results = await cur.fetchall()
            return [
                {
                    "id": row[0],
                    "user_id": row[1],
                    "amount": row[2],
                    "type": row[3],
                    "date": row[4],
                    "payment_id": row[5],
                    "created_at": row[6],
                    "updated_at": row[7],
                } for row in results
            ]

    @staticmethod
    async def get_wallet_balance(db: psycopg.AsyncConnection,
                                 user_id: int) -> Optional[Decimal]:
        """Get user wallet balance."""
        async with db.cursor() as cur:
            await cur.execute(
                "SELECT wallet_balance FROM users WHERE id = %s AND deleted_at IS NULL",
                (user_id, ),
            )

            result = await cur.fetchone()
            return result[0] if result else None

    @staticmethod
    async def top_up_wallet(
        db: psycopg.AsyncConnection,
        user_id: int,
        amount: Decimal,
        payment_type: str = "electronic",
    ) -> dict:
        """Top up user wallet."""
        # Create payment record first
        payment_data = PaymentCreate(amount=amount, payment_type=payment_type)
        payment = await PaymentService.create_payment(db, payment_data)

        # Create transaction
        transaction_data = TransactionCreate(
            user_id=user_id, amount=amount, type="deposit", payment_id=payment["id"]
        )
        transaction = await TransactionService.create_transaction(db, transaction_data)

        # Update payment status to completed
        await PaymentService.update_payment_status(db, payment["id"], "completed")

        return {
            "transaction": transaction,
            "payment": payment,
            "new_balance": await TransactionService.get_wallet_balance(db, user_id),
        }

    @staticmethod
    async def process_trip_payment(
        db: psycopg.AsyncConnection, trip_id: int, amount: Decimal
    ) -> dict:
        """Process payment for a trip."""
        async with db.cursor() as cur:
            # Get trip details
            await cur.execute(
                "SELECT passenger_id, driver_id FROM trips WHERE id = %s AND deleted_at IS NULL",
                (trip_id, ),
            )

            trip_result = await cur.fetchone()
            if not trip_result:
                raise HTTPException(status_code=404, detail="Trip not found")

            passenger_id, driver_id = trip_result

            # Start transaction
            await cur.execute("BEGIN")

            try:
                # Create payment record
                payment_data = PaymentCreate(amount=amount, payment_type="electronic")
                payment = await PaymentService.create_payment(db, payment_data)

                # Deduct from passenger wallet
                passenger_transaction = TransactionCreate(
                    user_id=passenger_id,
                    amount=-amount,
                    type="trip_payment",
                    payment_id=payment["id"],
                )
                await TransactionService.create_transaction(db, passenger_transaction)

                # Add to driver wallet (minus platform fee)
                driver_amount = amount * Decimal("0.85")  # 15% platform fee
                if driver_id:
                    driver_transaction = TransactionCreate(
                        user_id=driver_id,
                        amount=driver_amount,
                        type="trip_payment",
                        payment_id=payment["id"],
                    )
                    await TransactionService.create_transaction(db, driver_transaction)

                # Update trip with payment
                await cur.execute(
                    """
                    UPDATE trips SET payment_id = %s, updated_at = %s
                    WHERE id = %s
                    """,
                    (payment["id"], datetime.now(), trip_id),
                )

                # Update payment status
                await PaymentService.update_payment_status(
                    db, payment["id"], "completed"
                )

                await cur.execute("COMMIT")

                return {
                    "payment": payment,
                    "passenger_amount": -amount,
                    "driver_amount": driver_amount if driver_id else 0,
                    "platform_fee": amount - driver_amount if driver_id else amount,
                }

            except Exception as e:
                await cur.execute("ROLLBACK")
                raise e
