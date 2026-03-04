import logging
import os

import httpx

from utils import validate_env

logger = logging.getLogger(__name__)

client: httpx.AsyncClient

timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=10)


async def _get_token() -> str:
    res = await client.post("/wf/auth", json={
        "key": os.environ["SELARTI_KEY"]
    })
    res.raise_for_status()
    data = res.json()
    return data["response"]["token"]


async def add_target(username: str):
    try:
        token = await _get_token()
        res = await client.post("/wf/add_target", json={
            "task": os.environ["SELARTI_TASK"],
            "target": f"@{username}"
        }, headers={
            "Authorization": f"Bearer {token}"
        })
        logger.debug(f"Selarti add_target response: {res.status_code}, {res.text}")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        logger.warning(f"Failed to add target in Selarti for @{username}: {e}")


def init_selarti():
    global client
    validate_env("SELARTI_HOST")
    validate_env("SELARTI_KEY")
    validate_env("SELARTI_TASK")

    selarti_host = os.environ["SELARTI_HOST"]
    if selarti_host.endswith("/"):
        selarti_host = selarti_host[:-1]

    client = httpx.AsyncClient(
        base_url=selarti_host,
        headers={
            "Accept": "*/*",
            "Content-Type": "application/json",
        },
        timeout=timeout
    )


async def stop_selarti():
    await client.aclose()
