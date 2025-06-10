# yapf: disable

from fastapi import APIRouter

from app.core import settings

from . import api
from .views import router as views_router

# yapf: enable

router = APIRouter(
    prefix="/admin", tags=["admin"], include_in_schema=settings.ENVIRONMENT == "local"
)

# Include API routes
router.include_router(api.router)
router.include_router(views_router)
