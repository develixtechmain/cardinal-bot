from fastapi import Request, APIRouter
from fastapi.responses import RedirectResponse

from db.refs import fetch_user_refs

router = APIRouter()

redirect_router = APIRouter()


@redirect_router.get("/{user_id}")
async def redirect(user_id: int):
    return RedirectResponse(url=f"https://t.me/CardinalAPP_bot/Cardinal?startapp=ref_{user_id}")


@router.get("/me")
async def fetch_refs(request: Request):
    return await fetch_user_refs(request.state.user_id)
