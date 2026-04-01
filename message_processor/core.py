import logging
import os

import httpx

from utils import validate_env

logger = logging.getLogger(__name__)

client: httpx.AsyncClient


async def send_recommendation_to_user(message, candidate, recommendation_id):
    try:
        payload = {"id": str(recommendation_id), "user_id": str(candidate["userId"]), "task_id": str(candidate["taskId"]), "text": message["text"], "message_created_at": message["created_at"]}

        if message["user_username"]:
            payload["username"] = message["user_username"]

        extra_headers = {}
        if message.get("correlation_id"):
            cid = str(message["correlation_id"])
            payload["correlation_id"] = cid
            extra_headers["X-Correlation-ID"] = cid

        resp = await client.post("/send", json=payload, headers=extra_headers)
        resp.raise_for_status()
    except Exception as e:
        raise Exception(f"Failed to send recommendation to user") from e


def init_core():
    global client

    validate_env("BACKEND_CORE_KEY")
    validate_env("BACKEND_CORE_HOST")

    client = httpx.AsyncClient(
        base_url=os.environ["BACKEND_CORE_HOST"] + "/api/finder/recommendations",
        headers={"Content-Type": "application/json", "X-API-KEY": os.environ["BACKEND_CORE_KEY"]},
        timeout=httpx.Timeout(connect=60.0, read=60.0, write=60.0, pool=10),
    )
