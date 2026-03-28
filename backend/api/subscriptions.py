import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.params import Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr, Field, model_validator

from consts import TransactionPayment
from service.subscriptions import (
    SubscriptionWebhook,
    WebhookStatus,
    check_purchase_for_user,
    complete_alpha_purchase_for_user,
    complete_robokassa_purchase_for_user,
    disable_recurrency_for_user,
    fetch_recurrency_by_user_id,
    fetch_subscription_by_user_id,
    handle_lava_webhook,
    init_purchase_for_user,
    purchase_from_user_balance,
    start_subscription_trial,
)

router = APIRouter()

logger = logging.getLogger(__name__)


class PurchaseRequest(BaseModel):
    months: int = Field(gt=0)
    email: Optional[EmailStr] = Field(default=None, max_length=254)
    payment_system: TransactionPayment

    @model_validator(mode="after")
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
async def subscription_trial(request: Request, subscription_id: uuid.UUID):
    return await start_subscription_trial(request.state.user_id, subscription_id)


@router.post("/purchase")
async def init_purchase(request: Request, purchase_request: PurchaseRequest):
    return await init_purchase_for_user(request.state.user_id, purchase_request)


@router.get("/purchase/alpha/complete")
async def complete_purchase(external_id: uuid.UUID = Query(..., alias="orderId")):
    try:
        await complete_alpha_purchase_for_user(external_id)
        return payment_html(True)
    except HTTPException:
        raise
    except Exception as e:
        return payment_html(False, e)


@router.get("/purchase/robokassa/complete/result")
async def complete_purchase(request: Request):
    try:
        await complete_robokassa_purchase_for_user(request)
        return payment_html(True)
    except HTTPException:
        raise
    except Exception as e:
        return payment_html(False, e)


@router.get("/purchase/robokassa/complete")
async def complete_purchase(request: Request):
    try:
        # FIXME
        return payment_html(True)
    except HTTPException:
        raise
    except Exception as e:
        return payment_html(False, e)


@router.get("/purchase/{trx_id}")
async def check_purchase(request: Request, trx_id: uuid.UUID):
    return await check_purchase_for_user(request.state.user_id, trx_id)


@router.post("/purchase/balance")
async def init_balance_purchase(request: Request):
    return await purchase_from_user_balance(request.state.user_id)


@router.get("/recurrency")
async def recurrency(request: Request):
    return await fetch_recurrency_by_user_id(request.state.user_id)


@router.delete("/recurrency")
async def disable_recurrency(request: Request):
    return await disable_recurrency_for_user(request.state.user_id)


@router.post("/webhook/lava")
async def handle_lava(request: LavaWebhook):
    status = WebhookStatus.from_lava(request.eventType, request.errorMessage)
    if not status:
        logger.error(f"Unexpected lava event: {request.eventType}")
        return None

    await handle_lava_webhook(SubscriptionWebhook(id=request.contractId, amount=request.amount, currency=request.currency, status=status, payment=TransactionPayment.LAVA, payment_timestamp=request.timestamp))
    return None


# fmt: off
def payment_html(success: bool, e = None) -> HTMLResponse:
    if success:
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
    else:
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
# fmt: on
