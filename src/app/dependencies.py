"""Authentication dependencies for the API."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .core.db import Database
from .core.security import decode_jwt_token
from .services.user_service import UserService, AdminService, DriverService

security = HTTPBearer()


async def get_current_user(
    db: Database,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Get current authenticated user."""
    try:
        payload = decode_jwt_token(credentials.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    user = await UserService.get_user_by_id(db, int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    if user.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is not active",
        )

    return user


async def get_current_driver(
    db: Database, current_user: dict = Depends(get_current_user)
) -> dict:
    """Get current authenticated driver."""
    driver = await DriverService.get_driver_by_user_id(db, current_user["id"])
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User is not a driver"
        )

    if driver.get("approval_status") != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Driver is not approved"
        )

    return driver


async def get_current_admin(
    db: Database, current_user: dict = Depends(get_current_user)
) -> dict:
    """Get current authenticated admin."""
    admin = await AdminService.get_admin_by_user_id(db, current_user["id"])
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User is not an admin"
        )

    return admin


async def get_current_superuser(
    current_admin: dict = Depends(get_current_admin),
) -> dict:
    """Get current authenticated superuser admin."""
    if current_admin.get("access_level") != "superuser":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Superuser access required"
        )

    return current_admin


# Optional authentication (for public endpoints that can work with or without auth)
async def get_current_user_optional(
    db: Database,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[dict]:
    """Get current user if authenticated, otherwise return None."""
    if not credentials:
        return None

    try:
        payload = decode_jwt_token(credentials.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            return None

        user = await UserService.get_user_by_id(db, int(user_id))
        if user is None or user.get("status") != "active":
            return None

        return user
    except Exception:
        return None
