"""FastAPI main application for Online Taxi Management System."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core import init_db, close_db
from app.routers.admin import api as admin_router
from app.routers.users import router as users_router
from app.routers.driver import api as driver_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Online Taxi Management System",
        description="A comprehensive taxi booking and management platform",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.mount("/css", StaticFiles(directory="css"), name="css")
    app.mount("/js", StaticFiles(directory="js"), name="js")

    # Include routers
    app.include_router(users_router, prefix="/users")
    app.include_router(driver_router, prefix="/driver")
    app.include_router(admin_router, prefix="/admin")

    return app


# Create the app instance
app = create_app()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Online Taxi Management System",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "online-taxi-api"}
