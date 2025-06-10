# yapf: disable

import log21
from fastapi import Request, APIRouter
from rich.console import Console
from fastapi.responses import HTMLResponse

from .core import app, settings, templates
from .routers import user_router, admin_router, driver_router

# yapf: enable

router = APIRouter(include_in_schema=False)

console = Console()
log21.basic_config(level="DEBUG" if settings.DEBUG else "INFO")


@router.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        "public/index.html",
        {
            "request": request,
        },
    )


# Include the routers in the app.
app.include_router(router)
app.include_router(admin_router)
app.include_router(user_router)
app.include_router(driver_router)


@app.exception_handler(404)
async def custom_404_handler(request: Request, _) -> HTMLResponse:
    return templates.TemplateResponse(
        "public/404.html", {"request": request}, status_code=404
    )


@app.exception_handler(500)
async def custom_500_handler(request: Request, exception: Exception) -> HTMLResponse:
    log21.error(f"{request.url}: {exception.__class__.__name__}: {exception}")
    console.print_exception()
    return templates.TemplateResponse(
        "public/500.html", {"request": request}, status_code=500
    )
