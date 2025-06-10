"""This module is used to import all the routers from the different modules and make
them available to the main application."""

from .auth import router as auth_router
from .user import router as user_router
from .admin import router as admin_router
from .driver import router as driver_router

__all__ = ["admin_router", "driver_router", "user_router", "auth_router"]
