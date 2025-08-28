import logging
import os

import httpx

from utils import validate_env

client: httpx.AsyncClient

timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=10)

logger = logging.getLogger(__name__)

offers = {
    4900: "",
    12500: "",
    42000: ""
}


async def init_purchase(email, amount):
    offer = offers.get(amount)
    if not offer:
        raise Exception("Unexpected amount for init purchase")

    try:
        res = await client.post("/v2/invoice", json={
            "email": str(email),
            "offerId": offer,
            "currency": "RUB"
        })
        logger.debug(f"Response status: {res.status_code}, Response: {res.text}")

        res.raise_for_status()
        response = res.json()

        if response['amountTotal']['amount'] != amount:
            raise Exception("Wrong amount from lava purchase")

        return {
            "id": response['id'],
            "url": response['paymentUrl']
        }
    except Exception as e:
        raise Exception(f"Failed to init lava purchase: {e}") from e


async def fetch_transaction_status(trx_id):
    try:
        resp = await client.get(f"/v2/invoices/{trx_id}")
        logger.debug(f"Response status: {resp.status_code}, Response: {resp.text}")

        resp.raise_for_status()
        response = resp.json()
        lava_status = response.get("status")
        if not lava_status:
            raise Exception(f"Failed to fetch lava transaction status for {trx_id}: no status")

        status = lava_status.lower()
        if status in ["new", "in_progress"]:
            return 'pending'
        elif status == 'completed':
            return 'completed'
        elif status == 'failed':
            return 'failed'
        else:
            raise Exception(f"Failed to fetch lava transaction status for {trx_id}: unexpected status {status}")
    except Exception as e:
        raise Exception(f"Failed to fetch lava transaction status: {e}") from e


def init_lava():
    global client

    validate_env("LAVA_KEY")

    client = httpx.AsyncClient(headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Api-Key": os.environ["LAVA_KEY"],
    }, timeout=timeout, base_url="https://gate.lava.top/api")


async def stop_lava():
    await client.aclose()
