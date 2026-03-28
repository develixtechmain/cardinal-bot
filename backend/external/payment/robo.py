import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal

import httpx
import robokassa
from fastapi import Request
from httpx import HTTPStatusError
from robokassa.exceptions import RobokassaRequestError
from robokassa.types import PaymentState

from consts import TransactionStatus, get_months_by_price
from utils import validate_env

client: robokassa.Robokassa
http_client: httpx.AsyncClient
timeout = httpx.Timeout(connect=60.0, read=60.0, write=60.0, pool=10)

logger = logging.getLogger(__name__)

durations = {1: 30, 3: 90, 12: 365}
receipt_template: dict[str, str | dict[str, str | int | Decimal]] = {
    "sno": "usn_income",
    "items": [{"name": "Cardinal PRO", "quantity": 1, "payment_method": "full_payment", "payment_object": "service", "tax": "none"}],
}


async def init_purchase(months, email, price, number):
    duration = durations.get(months)
    if not duration:
        raise ValueError(f"Unexpected {months} months for init robokassa purchase")

    try:
        receipt = receipt_template.copy()
        name = f"Cardinal PRO — доступ {duration} дней"
        receipt["items"][0]["name"] = name
        receipt["items"][0]["cost"] = price
        receipt["items"][0]["sum"] = price
        expiration = datetime.now().astimezone() + timedelta(hours=1)
        payment_url = client.generate_open_payment_link(out_sum=price, email=str(email), description=name, inv_id=number, recurring=True, expiration_date=expiration, receipt=receipt)
        logger.info(f"{payment_url.params.signature_value}")

        return {"url": payment_url.url}
    except Exception as e:
        raise Exception(f"Failed to init robokassa purchase") from e


async def init_recurrent_purchase(original_trx, new_trx):
    months = get_months_by_price(original_trx["amount"])

    duration = durations.get(months)
    if not duration:
        raise ValueError(f"Unexpected {months} months for init robokassa purchase")

    price = original_trx["amount"]
    number = new_trx["number"]
    original_number = original_trx["number"]

    try:
        receipt = receipt_template.copy()
        name = f"Cardinal PRO — доступ {duration} дней"
        receipt["items"][0]["name"] = name
        receipt["items"][0]["cost"] = price
        receipt["items"][0]["sum"] = price
        payment = client.generate_subscription_link(out_sum=price, inv_id=number, previous_inv_id=original_number, receipt=receipt)

        data = {
            "MerchantLogin": payment.params.merchant_login,
            "InvoiceID": payment.params.inv_id,
            "PreviousInvoiceID": payment.params.previous_inv_id,
            "Description": name,
            "SignatureValue": payment.params.signature_value,
            "OutSum": payment.params.out_sum,
        }

        response = await http_client.post("/Recurring", data=data)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"{response.json()["detail"]}")
    except Exception as e:
        raise Exception(f"Failed to init robokassa recurrent purchase: {e}")


async def complete_purchase(request: Request):
    params = dict(request.query_params)
    result_data = {"out_sum": params.get("OutSum", ""), "inv_id": params.get("InvId", ""), "signature_value": params.get("SignatureValue", "")}
    logger.info(f"WITH LOWER: {client.is_result_notification_valid(signature=result_data["signature_value"].lower(), out_sum=result_data['out_sum'], inv_id=result_data['inv_id'])}")
    logger.info(f"WITHOUT LOWER: {client.is_result_notification_valid(signature=result_data["signature_value"], out_sum=result_data['out_sum'], inv_id=result_data['inv_id'])}")
    return client.is_result_notification_valid(signature=result_data["signature_value"], out_sum=result_data["out_sum"], inv_id=result_data["inv_id"]), result_data


async def fetch_transaction_status(inv_id) -> TransactionStatus:
    try:
        details = await client.get_payment_details(inv_id)

        state = details.state
        if not state:
            raise Exception(f"Failed to fetch robokassa transaction status for {inv_id}: no status")

        if state == PaymentState.COMPLETED:
            return TransactionStatus.COMPLETED
        if state in [PaymentState.INITIATED, PaymentState.PENDING]:
            return TransactionStatus.PENDING
        elif state in [PaymentState.CANCELLED, PaymentState.FAILED, PaymentState.SUSPENDED]:
            return TransactionStatus.FAILED
        else:
            raise Exception(f"Failed to fetch robokassa transaction status for {inv_id}: unexpected state {state}")
    except HTTPStatusError as e:
        if e.response.status_code == 404:
            return TransactionStatus.FAILED
        else:
            raise Exception(f"Failed to fetch robokassa transaction status") from e
    except RobokassaRequestError as e:
        if str(e).endswith("InvoiceId not found"):
            logger.warning(f"Failed to fetch robokassa transaction status: Unknown InvoiceId {inv_id}")
            return TransactionStatus.FAILED
        raise
    except Exception as e:
        raise Exception(f"Failed to fetch robokassa transaction status") from e


def init_robokassa():
    global client, http_client

    validate_env("ROBOKASSA_PASS_1")
    validate_env("ROBOKASSA_PASS_2")
    is_test = os.environ.get("ROBOKASSA_TEST", False)

    client = robokassa.Robokassa(merchant_login="cardinalx", password1=os.environ["ROBOKASSA_PASS_1"], password2=os.environ["ROBOKASSA_PASS_2"], algorithm=robokassa.HashAlgorithm.sha512, is_test=is_test)
    http_client = httpx.AsyncClient(base_url="https://auth.robokassa.ru/Merchant", timeout=timeout)
