from typing import Optional

from fastapi import Request, APIRouter
from pydantic import BaseModel

from db import fetch_user_by_id, patch_user_by_id

router = APIRouter()


class PatchUserRequest(BaseModel):
    username: Optional[str] = None
    avatar_url: str


@router.get("/me")
async def fetch_me(request: Request):
    return await fetch_user_by_id(request.state.user_id)


@router.patch("/me")
async def update_me(request: Request, patch: PatchUserRequest):
    return await patch_user_by_id(request.state.user_id, patch)
