import logging
import os

import httpx

from utils import validate_env

logger = logging.getLogger(__name__)

client: httpx.AsyncClient


async def send_recommendation_to_user(recommendation, candidate):
    try:
        resp = await client.post("/send", json={
            "id": recommendation["id"],
            "user_id": candidate['id'],
            "task_id": candidate['taskId'],
            "username": recommendation['username'],
            "text": recommendation['text']
        })
        logger.debug(f"Response status: {resp.status_code}, Response: {resp.text}")
        resp.raise_for_status()
    except Exception as e:
        raise Exception(f"Failed to send recommendation to user: {e}")


def init_core():
    global client

    validate_env("CORE_KEY")
    validate_env("CORE_HOST")

    client = httpx.AsyncClient(base_url=os.environ["CORE_HOST"] + "/api/finder/recommendations", headers={
        "Content-Type": "application/json",
        "X-API-KEY": os.environ["CORE_KEY"],
    }, timeout=httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=10))
