"""Admin template views."""

from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse

from app.core import templates

router = APIRouter(tags=["admin-views"])


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin dashboard template."""
    return templates.TemplateResponse("admin/base.html", {"request": request})


@router.get("/users/", response_class=HTMLResponse)
async def admin_users(request: Request):
    """Admin users page template."""
    return templates.TemplateResponse("admin/users.html", {"request": request})


@router.get("/drivers/", response_class=HTMLResponse)
async def admin_drivers(request: Request):
    """Admin drivers page template."""
    return templates.TemplateResponse("admin/drivers.html", {"request": request})


@router.get("/trips/", response_class=HTMLResponse)
async def admin_trips(request: Request):
    """Admin trips page template."""
    return templates.TemplateResponse("admin/trips.html", {"request": request})


@router.get("/payments/", response_class=HTMLResponse)
async def admin_payments(request: Request):
    """Admin payments page template."""
    return templates.TemplateResponse("admin/payments.html", {"request": request})


@router.get("/provinces/", response_class=HTMLResponse)
async def admin_provinces(request: Request):
    """Admin provinces page template."""
    return templates.TemplateResponse("admin/provinces.html", {"request": request})


@router.get("/cities/", response_class=HTMLResponse)
async def admin_cities(request: Request):
    """Admin cities page template."""
    return templates.TemplateResponse("admin/cities.html", {"request": request})


@router.get("/discounts/", response_class=HTMLResponse)
async def admin_discounts(request: Request):
    """Admin discounts page template."""
    return templates.TemplateResponse("admin/discounts.html", {"request": request})
