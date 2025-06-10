"""Main driver routes file."""
# yapf: disable

from fastapi import APIRouter

from app.core import settings

from .api import router as api_router
from .views import router as views_router

# yapf: enable

router = APIRouter(
    prefix="/driver",
    tags=["driver"],
    include_in_schema=settings.ENVIRONMENT == "local"
)
router.include_router(api_router)
router.include_router(views_router)
