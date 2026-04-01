import logging
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Request
from pydantic import BaseModel

from config import admin_login, admin_password, jwt_expiry_hours, jwt_secret

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"


class LoginRequest(BaseModel):
    login: str
    password: str


class LoginResponse(BaseModel):
    token: str
    expires_at: str


def create_token(login: str) -> tuple[str, datetime]:
    expires = datetime.now(timezone.utc) + timedelta(hours=jwt_expiry_hours())
    payload = {"sub": login, "exp": expires}
    token = jwt.encode(payload, jwt_secret(), algorithm=ALGORITHM)
    return token, expires


def authenticate(login: str, password: str) -> str | None:
    expected_login = admin_login()
    expected_password = admin_password()
    if not expected_password:
        logger.error("ADMIN_PASSWORD is not set")
        return None
    if login == expected_login and password == expected_password:
        token, _ = create_token(login)
        return token
    return None


def verify_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        cookie_token = request.cookies.get("admin_token")
        if not cookie_token:
            raise HTTPException(status_code=401, detail="Missing authorization")
        token = cookie_token
    else:
        token = auth[7:]
    try:
        payload = jwt.decode(token, jwt_secret(), algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
