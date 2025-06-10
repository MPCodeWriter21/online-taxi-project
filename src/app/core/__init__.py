# yapf: disable

import base64
import random

from fastapi import FastAPI
from fastapi.security import HTTPBearer
from fastapi.templating import Jinja2Templates
from cryptography.fernet import Fernet
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .db import get_db, init_db_pool, close_db_pool
from .config import settings
from .security import (csrf_serializer, verify_password, create_jwt_token,
                       decode_jwt_token, get_password_hash)

# yapf: enable

__all__ = [
    "app",
    "settings",
    "csrf_serializer",
    "create_jwt_token",
    "decode_jwt_token",
    "http_bearer",
    "verify_password",
    "get_password_hash",
    "get_db",
    "fernet",
    "templates",
]

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(GZipMiddleware, minimum_size=1000)
templates = Jinja2Templates("templates")
templates.env.globals["DEBUG"] = settings.DEBUG
templates.env.globals["SITE_DOMAIN"] = settings.DOMAIN
templates.env.globals["SITE_URL"] = settings.site_url
templates.env.globals["TAG"] = base64.b32encode(random.randbytes(8)).decode().strip("=")
templates.env.globals["abs"] = abs
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/js", StaticFiles(directory="js"), name="js")
app.mount("/css", StaticFiles(directory="css"), name="css")

# Security scheme for JWT bearer tokens
http_bearer = HTTPBearer()

fernet = Fernet(settings.FERNET_SECRET_KEY)


# Database pool lifecycle
@app.on_event("startup")
async def startup_event():
    """Initialize database pool on startup."""
    await init_db_pool()


@app.on_event("shutdown")
async def shutdown_event():
    """Close database pool on shutdown."""
    await close_db_pool()
