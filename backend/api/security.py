import hashlib
import hmac
import json
import os
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Callable
from uuid import UUID

import jwt
from fastapi import Request, HTTPException
from starlette.responses import JSONResponse

from utils import validate_env

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
INVALID_INIT_DATA = "Invalid Telegram init data"
SUBSCRIPTION_LAVA_KEY_PATHS = {"/api/subscription/webhook/lava"}
KEY_PATHS = {"/api/finder/recommendations/send"}
OPEN_PATHS = {"/r/*"}
WEBHOOK_PATHS = {"/api/webhook", "/api/finder/recommendations/webhook"}
EXCLUDED_PATHS = {"/api/auth", "/api/auth/refresh", "/docs", "/openapi.json", "/metrics", *KEY_PATHS, *SUBSCRIPTION_LAVA_KEY_PATHS, *WEBHOOK_PATHS}

lava_key: str
webhook_key: str
api_key: str
bot_token: str
jwt_secret_key: str


async def webhook_auth_middleware(request: Request, call_next: Callable):
    if not request.url.path in WEBHOOK_PATHS:
        return await call_next(request)

    key_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if not key_header or not webhook_key == key_header:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    return await call_next(request)


async def lava_auth_middleware(request: Request, call_next: Callable):
    if not request.url.path in SUBSCRIPTION_LAVA_KEY_PATHS:
        return await call_next(request)

    key_header = request.headers.get("X-Api-Key")
    if not key_header or not lava_key == key_header:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    return await call_next(request)


async def key_auth_middleware(request: Request, call_next: Callable):
    if not request.url.path in KEY_PATHS:
        return await call_next(request)

    key_header = request.headers.get("X-API-KEY")
    if not key_header or not api_key == key_header:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    return await call_next(request)


async def jwt_auth_middleware(request: Request, call_next: Callable):
    path = request.url.path
    if path.endswith("/"):
        path = path[:-1]

    if path in EXCLUDED_PATHS:
        return await call_next(request)

    for full_path in OPEN_PATHS:
        open_path = full_path.split("/*")[0]
        if path.startswith(open_path):
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


def authenticate_user(init_data: str):
    data = dict(urllib.parse.parse_qsl(init_data))

    for key in ["user", "auth_date", "hash"]:
        if key not in data:
            raise HTTPException(status_code=401, detail=INVALID_INIT_DATA)

    received_hash = data.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail=INVALID_INIT_DATA)

    params_without_hash = [(k, v) for k, v in data.items() if k != "hash"]
    params_sorted = sorted(params_without_hash, key=lambda x: x[0])
    data_check_string = "\n".join(f"{k}={v}" for k, v in params_sorted)

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(hmac_hash, received_hash):
        raise HTTPException(status_code=401, detail=INVALID_INIT_DATA)

    return json.loads(data['user']), data.get('start_param', None)


def create_token(user):
    return {
        "access_token": generate_access_token(user['id']),
        "refresh_token": generate_refresh_token(user['id'])
    }


def generate_access_token(user_id: str):
    return _generate_token(user_id, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


def generate_refresh_token(user_id: str):
    return _generate_token(user_id, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))


def _generate_token(user_id: str, time_delta: timedelta):
    return generate_token({"iss": "backend", "aud": "cardinal", "sub": user_id}, time_delta)


def generate_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    for key, value in to_encode.items():
        if isinstance(value, UUID):
            to_encode[key] = str(value)
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    to_encode.update({"iat": now, "exp": int(expire.timestamp())})
    return jwt.encode(to_encode, jwt_secret_key, algorithm=ALGORITHM)


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
    global jwt_secret_key, bot_token, api_key, webhook_key
    validate_env("SECURITY_KEY")
    jwt_secret_key = os.environ["SECURITY_KEY"]
    validate_env("BOT_TOKEN")
    bot_token = os.environ["BOT_TOKEN"]
    validate_env("API_KEY")
    api_key = os.environ["API_KEY"]
    validate_env("WEBHOOK_KEY")
    webhook_key = os.environ["WEBHOOK_KEY"]
    validate_env("LAVA_X_KEY")
    lava_key = os.environ["LAVA_X_KEY"]
