import logging
import os

import httpx

from utils import validate_env

core_send_recommendation_url: str

headers: dict
timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=10)

logger = logging.getLogger(__name__)


async def send_recommendation_to_user(recommendation, candidate):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(core_send_recommendation_url, json={
                "id": recommendation["id"],
                "user_id": candidate['id'],
                "username": recommendation['username'],
                "text": recommendation['text']
            }, headers=headers, timeout=timeout)
            logger.debug(f"Response status: {resp.status_code}, Response: {resp.text}")
            resp.raise_for_status()
        except Exception as e:
            raise Exception(f"Failed to send recommendation to user: {e}")


def init_core():
    global core_send_recommendation_url, headers

    validate_env("CORE_KEY")
    validate_env("CORE_HOST")
    core_send_recommendation_url = os.environ["CORE_HOST"] + "/api/finder/recommendations/"

    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": os.environ["CORE_KEY"],
    }
