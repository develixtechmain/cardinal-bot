import logging
import os
import string

import httpx

from utils import validate_env

embedder_save_tags_url: string

headers: dict
timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=10)

logger = logging.getLogger(__name__)

async def save_tags(user_id, tags):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(embedder_save_tags_url, json={
                "tags": tags,
                "taskId": str(user_id),
                "userId": str(user_id)
            }, headers=headers, timeout=timeout)
            logger.debug(f"Response status: {resp.status_code}, Response: {resp.text}")
            resp.raise_for_status()
        except Exception as e:
            raise Exception(f"Failed to save user tags: {e}")


def init_embedding():
    global embedder_save_tags_url, headers

    validate_env("EMBEDDER_KEY")
    validate_env("EMBEDDER_HOST")
    embedder_save_tags_url = os.environ["EMBEDDER_HOST"] + "/api/vectors/tags"

    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": os.environ["EMBEDDER_KEY"],
    }
