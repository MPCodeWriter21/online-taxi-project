"""Command-line management script for the taxi app."""

import sys
import asyncio
import getpass
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

import log21

from app.core.db import get_db, init_db_pool, close_db_pool
from app.core.config import settings
from app.schemas.user import UserCreate, AdminCreate
from app.core.migrations import migrate, rollback
from app.services.user_service import UserService, AdminService


async def runserver(host="127.0.0.1", port=8000, reload=True):
    """Run the FastAPI development server."""
    import uvicorn

    # Initialize database pool
    await init_db_pool()

    try:
        uvicorn.run(
            "app:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info" if settings.DEBUG else "warning",
        )
    finally:
        await close_db_pool()


async def create_superuser():
    """Create a superuser admin account."""

    # Get user input
    name = input("Name: ")
    phone = input("Phone: ")
    email = input("Email (optional): ") or None
    password = getpass.getpass("Password: ")
    confirm_password = getpass.getpass("Confirm password: ")

    if password != confirm_password:
        log21.error("Passwords do not match!")
        return False

    try:
        await init_db_pool()
        db = await get_db()

        # Create user
        user_data = UserCreate(name=name, phone=phone, email=email, password=password)

        user = await UserService.create_user(db, user_data)

        # Create admin with superuser privileges
        admin_data = AdminCreate(
            user_id=user["id"],
            permissions={
                "users": ["create", "read", "update", "delete"],
                "drivers": ["create", "read", "update", "delete"],
                "trips": ["create", "read", "update", "delete"],
                "payments": ["create", "read", "update", "delete"],
                "locations": ["create", "read", "update", "delete"],
                "discounts": ["create", "read", "update", "delete"],
                "tariffs": ["create", "read", "update", "delete"],
                "analytics": ["read"],
            },
            is_superuser=True,
        )

        admin = await AdminService.create_admin(db, admin_data)

        log21.success("Superuser created successfully!")
        log21.info(f"User ID: {user['id']}")
        log21.info(f"Admin ID: {admin['id']}")

        return True

    except Exception as e:
        log21.error(f"Error creating superuser: {e}")
        return False
    finally:
        await close_db_pool()


async def create_admin():
    """Create a regular admin account."""

    # Get user input
    name = input("Name: ")
    phone = input("Phone: ")
    email = input("Email (optional): ") or None
    password = getpass.getpass("Password: ")
    confirm_password = getpass.getpass("Confirm password: ")

    if password != confirm_password:
        log21.error("Passwords do not match!")
        return False

    # Get permissions
    log21.info("Select permissions (y/n):")
    permissions = {}

    modules = [
        "users",
        "drivers",
        "trips",
        "payments",
        "locations",
        "discounts",
        "tariffs",
    ]
    actions = ["create", "read", "update", "delete"]

    for module in modules:
        module_perms = []
        for action in actions:
            response = input(f"{module}.{action} (y/n): ").lower()
            if response in ["y", "yes"]:
                module_perms.append(action)

        if module_perms:
            permissions[module] = module_perms

    # Analytics is read-only
    analytics_perm = input("analytics.read (y/n): ").lower()
    if analytics_perm in ["y", "yes"]:
        permissions["analytics"] = ["read"]

    try:
        await init_db_pool()
        db = await get_db()

        # Create user
        user_data = UserCreate(name=name, phone=phone, email=email, password=password)

        user = await UserService.create_user(db, user_data)

        # Create admin
        admin_data = AdminCreate(
            user_id=user["id"], permissions=permissions, is_superuser=False
        )

        admin = await AdminService.create_admin(db, admin_data)

        log21.success("Admin created successfully!")
        log21.info(f"User ID: {user['id']}")
        log21.info(f"Admin ID: {admin['id']}")
        log21.info(f"Permissions: {permissions}")

        return True

    except Exception as e:
        log21.error(f"Error creating admin: {e}")
        return False
    finally:
        await close_db_pool()


async def init_database():
    """Initialize the database with migrations."""
    print("Initializing database...")
    try:
        await migrate()
        print("Database initialized successfully!")
        return True
    except Exception as ex:
        print(f"Error initializing database: {ex}")
        return False


async def run_migrations():
    """Run database migrations."""
    print("Running migrations...")
    try:
        await migrate()
        return True
    except Exception as ex:
        print(f"Error running migrations: {ex}")
        return False


async def rollback_migration():
    """Rollback last migration."""
    print("Rolling back last migration...")
    try:
        await rollback()
        return True
    except Exception as ex:
        print(f"Error rolling back migration: {ex}")
        return False


def create_parser():
    """Create the argument parser with colored output."""
    parser = log21.ColorizingArgumentParser(
        prog="manage.py",
        description="Taxi Management System CLI",
    )
    subparsers = parser.add_subparsers(
        dest="command", help="Available commands", metavar="COMMAND"
    )

    # Database commands
    subparsers.add_parser("init-db", help="Initialize database with migrations")
    subparsers.add_parser("migrate", help="Run pending database migrations")
    subparsers.add_parser("rollback", help="Rollback last migration")

    # User management commands
    subparsers.add_parser("create-superuser", help="Create a superuser admin account")
    subparsers.add_parser("create-admin", help="Create a regular admin account")

    return parser


async def main():
    """Main CLI entry point."""
    # Configure log21 colors
    log21.basic_config(level="INFO")

    parser = create_parser()

    if len(sys.argv) < 2:
        parser.print_help()
        return

    args = parser.parse_args()

    if args.command == "init-db":
        log21.info("Initializing database...")
        await init_database()
    elif args.command == "migrate":
        log21.info("Running migrations...")
        await run_migrations()
    elif args.command == "rollback":
        log21.warning("Rolling back last migration...")
        await rollback_migration()
    elif args.command == "create-superuser":
        log21.info("Creating superuser account...")
        await create_superuser()
    elif args.command == "create-admin":
        log21.info("Creating admin account...")
        await create_admin()
    else:
        log21.error(f"Unknown command: {args.command}")
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
