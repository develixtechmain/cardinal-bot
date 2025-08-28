from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.security import authenticate_user, create_token, parse_user_id
from db import fetch_user_by_id, create_user

router = APIRouter()


class AuthRequest(BaseModel):
    init_data: str


class AuthRefreshRequest(BaseModel):
    refresh_token: str


@router.post("/")
async def auth(request: AuthRequest):
    tg_user, ref = authenticate_user(request.init_data)
    try:
        user = await fetch_user_by_id(tg_user['id'], True)
    except HTTPException as e:
        if e.status_code == 404:
            if ref is None:
                user = await create_user(tg_user)
            else:
                ref_tg_id = ref[4:]
                ref_user = await fetch_user_by_id(ref_tg_id, True)
                user = await create_user(tg_user, ref_user['id'])
        else:
            raise e
    return create_token(user)


@router.post("/refresh")
async def refresh_token(request: AuthRefreshRequest):
    user_id = parse_user_id(request.refresh_token)
    user = await fetch_user_by_id(user_id)
    return create_token(user)
