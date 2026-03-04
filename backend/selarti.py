import logging
import os

import httpx

from utils import validate_env

logger = logging.getLogger(__name__)

auth_client: httpx.AsyncClient
target_client: httpx.AsyncClient

timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=10)


async def _get_token() -> str:
    res = await auth_client.post("/wf/auth", json={
        "key": os.environ["SELARTI_KEY"]
    })
    res.raise_for_status()
    data = res.json()
    return data["response"]["token"]


async def add_target(username: str):
    try:
        token = await _get_token()
        res = await target_client.post("/wf/add_target", json={
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
    global auth_client, target_client
    validate_env("SELARTI_AUTH_HOST")
    validate_env("SELARTI_TARGET_HOST")
    validate_env("SELARTI_KEY")
    validate_env("SELARTI_TASK")

    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
    }

    auth_host = os.environ["SELARTI_AUTH_HOST"]
    if auth_host.endswith("/"):
        auth_host = auth_host[:-1]

    target_host = os.environ["SELARTI_TARGET_HOST"]
    if target_host.endswith("/"):
        target_host = target_host[:-1]

    auth_client = httpx.AsyncClient(
        base_url=auth_host,
        headers=headers,
        timeout=timeout
    )

    target_client = httpx.AsyncClient(
        base_url=target_host,
        headers=headers,
        timeout=timeout
    )


async def stop_selarti():
    await auth_client.aclose()
    await target_client.aclose()
