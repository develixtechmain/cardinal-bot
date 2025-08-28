import uuid
from typing import Optional

from fastapi import Request, APIRouter
from pydantic import BaseModel, Field, EmailStr, model_validator

from db import fetch_subscription_by_user_id, start_subscription_trial, init_purchase_for_user

router = APIRouter()


class PurchaseRequest(BaseModel):
    amount: int = Field(gt=0)
    email: Optional[EmailStr] = Field(default=None, max_length=254)
    payment_system: str

    @model_validator(mode='after')
    def check_email_required_for_lava(self):
        if self.payment_system == 'lava' and not self.email:
            raise ValueError("Email must be included for lava payment_system")
        return self


@router.get("/me")
async def fetch_subscription(request: Request):
    return await fetch_subscription_by_user_id(request.state.user_id)


@router.post("/{subscription_id}/trial")
async def patch_task(request: Request, subscription_id: uuid.UUID):
    return await start_subscription_trial(request.state.user_id, subscription_id)


@router.post("/purchase")
async def init_purchase(request: Request, purchase_request: PurchaseRequest):
    return await init_purchase_for_user(request.state.user_id, purchase_request)
