# yapf: disable

from fastapi import APIRouter

from .views import router as views_router
from .api_v1 import router as api_v1_router

# yapf: enable

router = APIRouter(tags=["vendor"])
html_router = APIRouter(include_in_schema=False)

# Include API routes
router.include_router(api_v1_router)
router.include_router(views_router)
