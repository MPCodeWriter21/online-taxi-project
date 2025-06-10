"""Centralized authentication routes for all user types."""

from fastapi import Form, Depends, Request, APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core import templates
from app.core.db import Database
from app.dependencies import get_current_user, get_current_admin, get_current_driver
from app.schemas.user import UserCreate, DriverCreate
from app.core.security import create_jwt_token
from app.services.user_service import UserService, AdminService, DriverService

router = APIRouter(tags=["auth"], include_in_schema=False, prefix="/auth")


# Login page routes
@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request, type: str = "user", redirect: str = None, message: str = None
):
    """Unified login page for all user types."""
    context = {
        "request": request,
        "user_type": type,
        "redirect_url": redirect,
        "message": message
    }
    return templates.TemplateResponse("auth/login.html", context)


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, type: str = "user"):
    """Unified registration page for users and drivers."""
    if type == "admin":
        # Admins can only be created by other admins
        raise HTTPException(status_code=404, detail="Page not found")

    context = {"request": request, "user_type": type}
    return templates.TemplateResponse("auth/register.html", context)


# API endpoints for authentication
@router.post("/api/login")
async def login_api(
    db: Database,
    user_type: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    redirect_url: str = Form(None),
):
    """API endpoint for login."""
    try:
        # Authenticate based on user type
        if user_type == "user":
            user = await UserService.authenticate_user(db, phone, password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect phone or password"
                )
            redirect_default = "/user/"

        elif user_type == "driver":
            user = await UserService.authenticate_user(db, phone, password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect phone or password"
                )

            # Check if user is a driver
            driver = await DriverService.get_driver_by_user_id(db, user["id"])
            if not driver:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not registered as a driver"
                )

            if driver.get("approval_status") != "approved":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Driver account is not approved yet"
                )

            redirect_default = "/driver/"

        elif user_type == "admin":
            user = await UserService.authenticate_user(db, phone, password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect phone or password"
                )

            # Check if user is an admin
            admin = await AdminService.get_admin_by_user_id(db, user["id"])
            if not admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not an admin"
                )

            redirect_default = "/admin/"

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user type"
            )

        # Create JWT token
        access_token = create_jwt_token(subject=str(user["id"]))

        # Set the redirect URL
        final_redirect = redirect_url if redirect_url else redirect_default

        # Create response with redirect
        response = RedirectResponse(url=final_redirect, status_code=302)

        # Set auth token in cookie and return JSON for JavaScript
        response.set_cookie(
            key="authToken",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=7 * 24 * 60 * 60  # 7 days
        )

        return response

    except HTTPException:
        raise
    except Exception as ex:
        print(f"Login error: {ex}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/api/register")
async def register_api(
    db: Database,
    user_type: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    # Driver specific fields
    license_number: str = Form(None),
    vehicle_make: str = Form(None),
    vehicle_model: str = Form(None),
    vehicle_year: str = Form(None),
    license_plate: str = Form(None),
):
    """API endpoint for registration."""
    try:
        if user_type not in ["user", "driver"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user type"
            )  # Create user data
        full_name = f"{first_name} {last_name}".strip()
        user_data = UserCreate(
            name=full_name, phone=phone, email=email, password=password
        )

        # Create user
        user = await UserService.create_user(db, user_data)
        if user_type == "driver":
            # Create driver profile
            driver_data = DriverCreate(
                user_id=user["id"],
                license_number=license_number,
                car_info={
                    "make": vehicle_make,
                    "model": vehicle_model,
                    "year": vehicle_year,
                    "license_plate": license_plate
                }
            )
            await DriverService.create_driver(db, driver_data)

            # Redirect to driver dashboard with pending approval message
            redirect_url = (
                "/auth/login?type=driver&message="
                "Registration successful! Please wait for admin approval."
            )
            response = RedirectResponse(url=redirect_url, status_code=302)
        else:
            # Create JWT token for regular users
            access_token = create_jwt_token(subject=str(user["id"]))
            response = RedirectResponse(url="/user/", status_code=302)
            response.set_cookie(
                key="authToken",
                value=access_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=7 * 24 * 60 * 60  # 7 days
            )

        return response
    except Exception as ex:
        print(f"Registration error: {ex}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.get("/logout")
async def logout():
    """Logout endpoint."""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("authToken")
    return response


@router.get("/api/logout")
async def logout_api():
    """API logout endpoint."""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("authToken")
    return response


# Profile endpoints for token validation
@router.get("/api/profile/admin")
async def get_admin_profile(
    db: Database, current_admin: dict = Depends(get_current_admin)
):
    """Get admin profile for token validation."""
    return current_admin


@router.get("/api/profile/driver")
async def get_driver_profile(
    db: Database, current_driver: dict = Depends(get_current_driver)
):
    """Get driver profile for token validation."""
    return current_driver


@router.get("/api/profile/user")
async def get_user_profile(
    db: Database, current_user: dict = Depends(get_current_user)
):
    """Get user profile for token validation."""
    return current_user
