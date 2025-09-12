import json
import logging
import os
from collections import defaultdict

import httpx
from httpx import HTTPStatusError

from utils import validate_env

client: httpx.AsyncClient

timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=10)

logger = logging.getLogger(__name__)

prices = {
    1: 4900,
    3: 12500,
    12: 42000
}

periodicity = {
    1: "MONTHLY",
    3: "PERIOD_90_DAYS",
    12: "PERIOD_YEAR"
}


async def init_purchase(email, months):
    price = prices.get(months)
    if not price:
        raise Exception(f"Unexpected {months} months for init purchase")

    period = periodicity.get(months)

    try:
        res = await client.post("/v2/invoice", json={
            "email": str(email),
            "offerId": "52ed246e-b13c-46b9-b589-f0468dcbc299",
            "periodicity": period,
            "currency": "RUB"
        })
        logger.debug(f"Response status: {res.status_code}, Response: {res.text}")

        res.raise_for_status()
        response = res.json()

        if response['amountTotal']['amount'] != price:
            raise Exception("Wrong amount from lava purchase")

        return {
            "id": response['id'],
            "url": response['paymentUrl'],
            "price": price
        }
    except Exception as e:
        raise Exception(f"Failed to init lava purchase") from e


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
        raise Exception(f"Failed to fetch lava transaction status") from e


async def disable_recurrency_for_user(transactions: list):
    result = defaultdict(list)
    for trx in transactions:
        trx_id = trx['external_id']
        try:
            subscription = await _fetch_subscription(trx_id)
            await _disable_subscription(trx_id, subscription['buyer']['email'])
            result['success'].append(trx)
        except Exception as e:
            logger.warning(f"Failed to disable lava recurrent transaction {trx['id']}: {e}")
            result['failed'].append(trx)


async def _fetch_subscription(trx_id):
    try:
        resp = await client.get(f"/v2/subscriptions/{trx_id}")
        logger.debug(f"Response status: {resp.status_code}, Response: {resp.text}")

        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise Exception(f"Failed to fetch lava subscription {trx_id}") from e


async def _disable_subscription(trx_id, email):
    try:
        resp = await client.request(method="DELETE", url="/v2/subscriptions", headers={"Content-Type": "application/json"}, content=json.dumps(
            {
                "contractId": trx_id,
                "email": str(email)
            }))
        logger.debug(f"Response status: {resp.status_code}, Response: {resp.text}")

        resp.raise_for_status()
    except HTTPStatusError as e:
        if e.response.status_code != 404:
            raise Exception(f"Failed to disable lava subscription {trx_id}") from e
    except Exception as e:
        raise Exception(f"Failed to disable lava subscription {trx_id}") from e


def init_lava():
    global client

    validate_env("LAVA_KEY")

    client = httpx.AsyncClient(base_url="https://gate.lava.top/api", headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Api-Key": os.environ["LAVA_KEY"],
    }, timeout=timeout)


async def stop_lava():
    await client.aclose()
