"""Database migration system."""

import asyncio
from typing import List
from pathlib import Path

from psycopg_pool import AsyncConnectionPool

from app.core.config import settings


class MigrationManager:
    """Handles database migrations."""

    def __init__(self, pool: AsyncConnectionPool):
        self.pool = pool
        self.migrations_dir = Path(__file__).parent.parent.parent / "migrations"

    async def create_migrations_table(self):
        """Create migrations tracking table if it doesn't exist."""
        async with self.pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                    CREATE TABLE IF NOT EXISTS migrations (
                        id SERIAL PRIMARY KEY,
                        filename VARCHAR(255) NOT NULL UNIQUE,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
            )
            await conn.commit()

    async def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations."""
        async with self.pool.connection() as conn, conn.cursor() as cur:
            await cur.execute("SELECT filename FROM migrations ORDER BY id")
            results = await cur.fetchall()
            return [row[0] for row in results]

    async def get_pending_migrations(self) -> List[Path]:
        """Get list of pending migrations."""
        if not self.migrations_dir.exists():
            self.migrations_dir.mkdir(parents=True, exist_ok=True)
            return []

        applied = await self.get_applied_migrations()
        migration_files = sorted(
            [f for f in self.migrations_dir.glob("*.sql") if f.name not in applied]
        )

        return migration_files

    async def apply_migration(self, migration_file: Path):
        """Apply a single migration."""
        print(f"Applying migration: {migration_file.name}")

        async with self.pool.connection() as conn, conn.cursor() as cur:
            # Read and execute migration
            migration_sql = migration_file.read_text(encoding="utf-8")
            await cur.execute(migration_sql)

            # Record migration as applied
            await cur.execute(
                "INSERT INTO migrations (filename) VALUES (%s)",
                (migration_file.name, )
            )

            await conn.commit()

        print(f"Applied migration: {migration_file.name}")

    async def migrate(self):
        """Run all pending migrations."""
        await self.create_migrations_table()

        pending = await self.get_pending_migrations()
        if not pending:
            print("No pending migrations.")
            return

        print(f"Found {len(pending)} pending migrations.")

        for migration_file in pending:
            await self.apply_migration(migration_file)

        print("All migrations applied successfully.")

    async def rollback_last(self):
        """Rollback the last applied migration (if rollback file exists)."""
        async with self.pool.connection() as conn, conn.cursor() as cur:
            # Get last migration
            await cur.execute(
                "SELECT filename FROM migrations ORDER BY id DESC LIMIT 1"
            )
            result = await cur.fetchone()

            if not result:
                print("No migrations to rollback.")
                return

            last_migration = result[0]
            rollback_file = self.migrations_dir / f"rollback_{last_migration}"

            if not rollback_file.exists():
                print(f"No rollback file found for {last_migration}")
                return

            print(f"Rolling back migration: {last_migration}")

            # Execute rollback
            rollback_sql = rollback_file.read_text(encoding="utf-8")
            await cur.execute(rollback_sql)

            # Remove from migrations table
            await cur.execute(
                "DELETE FROM migrations WHERE filename = %s", (last_migration, )
            )

            await conn.commit()
            print(f"Rolled back migration: {last_migration}")


async def get_migration_manager() -> MigrationManager:
    """Get migration manager instance."""
    pool = AsyncConnectionPool(conninfo=settings.database_url, min_size=1, max_size=5)

    await pool.open()
    return MigrationManager(pool)


async def migrate():
    """CLI command to run migrations."""
    manager = await get_migration_manager()
    try:
        await manager.migrate()
    finally:
        await manager.pool.close()


async def rollback():
    """CLI command to rollback last migration."""
    manager = await get_migration_manager()
    try:
        await manager.rollback_last()
    finally:
        await manager.pool.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m app.core.migrations [migrate|rollback]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "migrate":
        asyncio.run(migrate())
    elif command == "rollback":
        asyncio.run(rollback())
    else:
        print("Unknown command. Use 'migrate' or 'rollback'")
        sys.exit(1)
