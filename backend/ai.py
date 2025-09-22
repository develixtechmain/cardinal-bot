import logging
import os

import httpx

from utils import validate_env

client: httpx.AsyncClient

timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=10)

logger = logging.getLogger(__name__)


async def check_rules(text: str, rules: list[str]):
    try:
        res = await client.post("/rules/check", json={
            "text": text,
            "rules": rules
        })
        logger.debug(f"Response status: {res.status_code}, Response: {res.text}")
        res.raise_for_status()
        return True
    except Exception as e:
        logger.warning(f"Failed to check message for rules: {e}")
        return False


async def extract_rules(text: str, user_text: str):
    try:
        res = await client.post("/rules/extract", json={
            "text": text,
            "userText": user_text
        })
        logger.debug(f"Response status: {res.status_code}, Response: {res.text}")
        res.raise_for_status()
        return res.json()
    except Exception as e:
        raise Exception(f"Failed to extract rule") from e


def init_ai():
    global client

    validate_env("AI_CORE_KEY")
    validate_env("AI_CORE_HOST")
    ai_core_host = os.environ["AI_CORE_HOST"]
    if ai_core_host.endswith("/"):
        ai_core_host = ai_core_host[:-1]

    client = httpx.AsyncClient(base_url=ai_core_host + "/api", headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-API-KEY": os.environ["AI_CORE_KEY"],
    }, timeout=timeout, verify=False)


async def stop_ai():
    await client.aclose()
