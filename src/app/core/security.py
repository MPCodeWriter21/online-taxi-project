"""This module contains core security utilities."""

from typing import Any
from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException
from itsdangerous import URLSafeTimedSerializer
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def create_jwt_token(
    subject: str | Any, expires_delta: timedelta = timedelta(days=7), **kwargs
) -> str:
    """Creates a JWT token with the specified subject.

    :param subject: The subject of the token.
    :param expires_delta: The expiration time of the token.
    :return: The JWT token.
    """
    expiration = datetime.now() + expires_delta
    payload = {"sub": subject, "exp": expiration, **kwargs}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_jwt_token(token: str) -> Any:
    """Decodes a JWT token and returns the subject.

    :param token: The token to decode.
    :raises HTTPException: If the token is invalid or expired.
    :return: The subject of the token.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("exp") < datetime.now().timestamp():
            raise jwt.ExpiredSignatureError()
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Token expired") from None
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid token") from None


# CSRF token serializer
csrf_serializer = URLSafeTimedSerializer(settings.CSRF_SECRET_KEY)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a password against a hashed password.

    :param plain_password: The plain password.
    :param hashed_password: The hashed password.
    :return: True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Returns the hashed password.

    :param password: The password to hash.
    :return: The hashed password.
    """
    return pwd_context.hash(password)
