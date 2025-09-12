import os
from typing import Callable

import jwt
from fastapi import Request, HTTPException
from starlette.responses import JSONResponse

from utils import validate_env

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

bot_token: str
jwt_secret_key: str

INVALID_INIT_DATA = "Invalid Telegram init data"
KEY_PATHS = {"/api/rules/check", "/api/rules/extract"}
EXCLUDED_PATHS = {"/docs", "/openapi.json", *KEY_PATHS}

api_key: str


async def key_auth_middleware(request: Request, call_next: Callable):
    if not request.url.path in KEY_PATHS:
        return await call_next(request)

    key_header = request.headers.get("X-API-KEY")
    if not key_header or not api_key == key_header:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    return await call_next(request)


async def jwt_auth_middleware(request: Request, call_next: Callable):
    if request.url.path in EXCLUDED_PATHS:
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    token = auth_header.split(" ")[1]
    try:
        user_id = parse_user_id(token)
        request.state.user_id = user_id
    except HTTPException:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    return await call_next(request)


def parse_user_id(token: str):
    try:
        payload = jwt.decode(token, jwt_secret_key, audience="cardinal", algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token: missing sub")
        return user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


def init_security():
    global jwt_secret_key, bot_token, api_key
    validate_env("SECURITY_KEY")
    jwt_secret_key = os.environ["SECURITY_KEY"]
    validate_env("BOT_TOKEN")
    bot_token = os.environ["BOT_TOKEN"]
    validate_env("API_KEY")
    api_key = os.environ["API_KEY"]
