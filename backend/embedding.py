import logging
import os

import httpx

from utils import validate_env

client: httpx.AsyncClient

timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=10)

logger = logging.getLogger(__name__)


async def save_tags(user_id, task_id, tags):
    try:
        resp = await client.post("/vectors/tags", json={
            "tags": tags,
            "taskId": str(task_id),
            "userId": str(user_id)
        })
        logger.debug(f"Response status: {resp.status_code}, Response: {resp.text}")
        if resp.status_code != 200:
            raise Exception(f"Save user tags failed with {resp.status_code}")
    except Exception as e:
        raise Exception(f"Failed to save user tags") from e


async def accept_recommendation(recommendation_id):
    try:
        resp = await client.patch(f"/api/learning/{recommendation_id}/success")
        logger.debug(f"Response status: {resp.status_code}, Response: {resp.text}")
        if resp.status_code != 200:
            raise Exception(f"Accept user recommendation failed with {resp.status_code}")
    except Exception as e:
        raise Exception(f"Failed to accept user recommendation") from e


async def decline_recommendation(recommendation_id):
    try:
        resp = await client.patch(f"/api/learning/{recommendation_id}/fail")
        logger.debug(f"Response status: {resp.status_code}, Response: {resp.text}")
        if resp.status_code != 200:
            raise Exception(f"Decline user recommendation failed with {resp.status_code}")
    except Exception as e:
        raise Exception(f"Failed to decline user recommendation") from e


def init_embedding():
    global client

    validate_env("EMBEDDINGS_PROCESSOR_KEY")
    validate_env("EMBEDDINGS_PROCESSOR_HOST")
    embedder_host = os.environ.get("EMBEDDINGS_PROCESSOR_HOST")
    if embedder_host.endswith("/"):
        embedder_host = embedder_host[:-1]

    client = httpx.AsyncClient(base_url=embedder_host + "/api", headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-API-KEY": os.environ["EMBEDDINGS_PROCESSOR_KEY"],
    }, timeout=timeout)


async def stop_embedding():
    await client.aclose()
