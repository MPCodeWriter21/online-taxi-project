"""This module contains core database utilities."""

import os.path
from typing import Annotated
from contextlib import asynccontextmanager

import psycopg
from fastapi import Depends
from psycopg_pool import AsyncConnectionPool

from .config import settings

# Global connection pool
_pool: AsyncConnectionPool | None = None


async def init_db_pool() -> None:
    """Initialize the database connection pool."""
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(settings.database_url, min_size=1, max_size=21)
        await _pool.open()


async def close_db_pool() -> None:
    """Close the database connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_db_connection():
    """Get a database connection from the pool."""
    global _pool
    if _pool is None:
        await init_db_pool()

    async with _pool.connection() as conn:
        yield conn


async def get_db():
    """Dependency to get a database connection."""
    async with get_db_connection() as conn:
        yield conn


async def init_db():
    """Initialize the database with the schema from base.sql."""

    # Read the base.sql file
    base_sql_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "base.sql"
    )

    async with get_db_connection() as conn:
        with open(base_sql_path, "r", encoding="utf-8") as file:
            sql = file.read()

        # Execute the SQL to create tables
        await conn.execute(sql)
        await conn.commit()


# Type annotation for database dependency
Database = Annotated[psycopg.AsyncConnection, Depends(get_db)]
