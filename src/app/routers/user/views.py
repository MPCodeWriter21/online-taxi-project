"""User template views."""

from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse

from app.core import templates

router = APIRouter(tags=["user-views"], prefix="/user")


@router.get("/", response_class=HTMLResponse)
async def user_dashboard(request: Request):
    """User dashboard template."""
    return templates.TemplateResponse("user/base.html", {"request": request})


@router.get("/trips", response_class=HTMLResponse)
async def user_trips(request: Request):
    """User trips page template."""
    return templates.TemplateResponse("user/trips.html", {"request": request})


@router.get("/wallet", response_class=HTMLResponse)
async def user_wallet(request: Request):
    """User wallet page template."""
    return templates.TemplateResponse("user/wallet.html", {"request": request})
