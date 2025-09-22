import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import Request, APIRouter
from fastapi.params import Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, EmailStr, model_validator

from service import fetch_subscription_by_user_id, start_subscription_trial, init_purchase_for_user, handle_webhook, SubscriptionWebhook, WebhookStatus, TransactionPayment, disable_recurrency_for_user, \
    purchase_from_user_balance, complete_purchase_for_user, check_purchase_for_user

router = APIRouter()

logger = logging.getLogger(__name__)


class PurchaseRequest(BaseModel):
    months: int = Field(gt=0)
    email: Optional[EmailStr] = Field(default=None, max_length=254)
    payment_system: TransactionPayment

    @model_validator(mode='after')
    def check_email_required_for_lava(self):
        if self.payment_system in (TransactionPayment.LAVA, TransactionPayment.ALPHA) and not self.email:
            raise ValueError("Email must be included for lava|alpha payment_system")
        return self


class LavaWebhook(BaseModel):
    contractId: uuid.UUID
    amount: int
    currency: str
    eventType: str
    errorMessage: Optional[str]
    timestamp: datetime


@router.get("/me")
async def fetch_subscription(request: Request):
    return await fetch_subscription_by_user_id(request.state.user_id)


@router.post("/{subscription_id}/trial")
async def patch_task(request: Request, subscription_id: uuid.UUID):
    return await start_subscription_trial(request.state.user_id, subscription_id)


@router.post("/purchase")
async def init_purchase(request: Request, purchase_request: PurchaseRequest):
    return await init_purchase_for_user(request.state.user_id, purchase_request)


@router.get("/purchase/complete")
async def complete_purchase(external_id: uuid.UUID = Query(..., alias="orderId")):
    try:
        await complete_purchase_for_user(external_id)
        return HTMLResponse("""
                <html>
                    <body>
                        <p>Успешный платёж</p>
                        <script>
                            setTimeout(() => window.close(), 1500);
                        </script>
                    </body>
                </html>
            """)

    except Exception as e:
        logger.warning(f"Failed to complete purchase: {e}")
        return HTMLResponse("""
                <html>
                    <body>
                        <p>Ошибка во время обработки платежа</p>
                        <script>
                            setTimeout(() => window.close(), 1500);
                        </script>
                    </body>
                </html>
            """)


@router.get("/purchase/{trx_id}")
async def check_purchase(request: Request, trx_id: uuid.UUID):
    return await check_purchase_for_user(request.state.user_id, trx_id)


@router.post("/purchase/balance")
async def init_balance_purchase(request: Request):
    return await purchase_from_user_balance(request.state.user_id)


@router.delete("/recurrency")
async def disable_recurrency(request: Request):
    return await disable_recurrency_for_user(request.state.user_id)


@router.post("/webhook/lava")
async def handle_lava(request: LavaWebhook):
    status = WebhookStatus.from_lava(request.eventType, request.errorMessage)
    if not status:
        logger.error(f"Unexpected lava event: {request.eventType}")
        return None

    await handle_webhook(
        SubscriptionWebhook(
            id=request.contractId,
            amount=request.amount,
            currency=request.currency,
            status=status,
            payment=TransactionPayment.LAVA,
            paymentTimestamp=request.timestamp
        ))
    return None
