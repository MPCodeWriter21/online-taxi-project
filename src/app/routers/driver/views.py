"""Driver template views."""

from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse

from app.core import templates

router = APIRouter(tags=["driver-views"], prefix="/driver")


@router.get("/", response_class=HTMLResponse)
async def driver_dashboard(request: Request):
    """Driver dashboard template."""
    return templates.TemplateResponse("driver/base.html", {"request": request})


@router.get("/trips/", response_class=HTMLResponse)
async def driver_trips(request: Request):
    """Driver trips page template."""
    return templates.TemplateResponse("driver/trips.html", {"request": request})


@router.get("/earnings/", response_class=HTMLResponse)
async def driver_earnings(request: Request):
    """Driver earnings page template."""
    return templates.TemplateResponse("driver/earnings.html", {"request": request})
