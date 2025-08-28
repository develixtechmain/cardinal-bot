import logging
import os

import httpx

from utils import validate_env

client: httpx.AsyncClient
embedder_save_tags_url: str

timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=10)

logger = logging.getLogger(__name__)


async def save_tags(user_id, tags):
    try:
        resp = await client.post(embedder_save_tags_url, json={
            "tags": tags,
            "taskId": str(user_id),
            "userId": str(user_id)
        })
        logger.debug(f"Response status: {resp.status_code}, Response: {resp.text}")
        if resp.status_code != 200:
            raise Exception(f"Save user tags failed with {resp.status_code}")
    except Exception as e:
        raise Exception(f"Failed to save user tags: {e}")


async def accept_recommendation(recommendation_id):
    try:
        resp = await client.patch(f"/api/learning/{recommendation_id}/success")
        logger.debug(f"Response status: {resp.status_code}, Response: {resp.text}")
        if resp.status_code != 200:
            raise Exception(f"Accept user recommendation failed with {resp.status_code}")
    except Exception as e:
        raise Exception(f"Failed to accept user recommendation: {e}")


async def decline_recommendation(recommendation_id):
    try:
        resp = await client.patch(f"/api/learning/{recommendation_id}/fail")
        logger.debug(f"Response status: {resp.status_code}, Response: {resp.text}")
        if resp.status_code != 200:
            raise Exception(f"Decline user recommendation failed with {resp.status_code}")
    except Exception as e:
        raise Exception(f"Failed to decline user recommendation: {e}")


def init_embedding():
    global embedder_save_tags_url, client

    validate_env("EMBEDDER_KEY")
    validate_env("EMBEDDER_HOST")
    embedder_host = os.environ.get("EMBEDDER_HOST")
    embedder_save_tags_url = embedder_host + "/api/vectors/tags"

    client = httpx.AsyncClient(headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-API-KEY": os.environ["EMBEDDER_KEY"],
    }, timeout=timeout, base_url=embedder_host)


async def stop_embedding():
    await client.aclose()
