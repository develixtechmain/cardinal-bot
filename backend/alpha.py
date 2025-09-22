import logging
import os

import httpx

from consts import TransactionStatus
from utils import validate_env

client: httpx.AsyncClient

timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=10)

logger = logging.getLogger(__name__)

verify_url: str

durations = {
    1: "1 мес.",
    3: "3 мес.",
    12: "год",
}


async def init_purchase(trx_id, months, email, price):
    duration = durations.get(months)
    if not duration:
        raise ValueError(f"Unexpected {months} months for init alpha purchase")
    try:
        url = f"{verify_url}/api/subscriptions/purchase/complete"
        res = await client.post("/register.do", params={
            "orderNumber": str(trx_id),
            "email": str(email),
            "amount": price * 100,
            "currency": 810,
            "description": f"CARDINAL PRO {duration}",
            "returnUrl": url,
            "failUrl": url
        })
        logger.debug(f"Response status: {res.status_code}, Response: {res.text}")

        res.raise_for_status()
        response = res.json()

        return {
            "id": response['orderId'],
            "url": response['formUrl']
        }
    except Exception as e:
        raise Exception(f"Failed to init alpha purchase") from e


async def fetch_order_status(order_id):
    try:
        res = await client.post("/getOrderStatusExtended.do", params={
            "orderId": order_id
        })
        logger.debug(f"Response status: {res.status_code}, Response: {res.text}")

        res.raise_for_status()
        response = res.json()
        status = response.get("orderStatus")
        if not status:
            error_code = response.get("errorCode")
            if error_code and int(error_code) == 6:
                return TransactionStatus.FAILED
            raise ValueError(f"No status")

        if status in (0, 1, 5):
            return TransactionStatus.PENDING
        elif status == 2:
            return TransactionStatus.COMPLETED
        elif status in [3, 4, 6]:
            return TransactionStatus.FAILED
        else:
            raise ValueError(f"Unexpected status {status}")
    except Exception as e:
        raise Exception(f"Failed to fetch alpha {order_id} order status") from e


def init_alpha():
    global client, verify_url

    validate_env("ALPHA_KEY")
    validate_env("WEBHOOK_URL")

    verify_url = os.environ["WEBHOOK_URL"]
    client = AuthAsyncClient(base_url="https://alfa.rbsuat.com/payment/rest", headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
    }, timeout=timeout, token=os.environ["ALPHA_KEY"])


class AuthAsyncClient(httpx.AsyncClient):
    def __init__(self, token: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._token = token

    async def post(self, url: str, *args, **kwargs):
        params = kwargs.get("params", {}) or {}
        params["token"] = self._token
        kwargs["params"] = params
        return await super().post(url, *args, **kwargs)


async def stop_alpha():
    await client.aclose()
