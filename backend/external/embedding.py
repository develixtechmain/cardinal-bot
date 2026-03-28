import logging
import os
import uuid

import httpx

from utils import validate_env

client: httpx.AsyncClient

timeout = httpx.Timeout(connect=60.0, read=60.0, write=60.0, pool=10)

logger = logging.getLogger(__name__)


async def save_tags(user_id, task_id, tags):
    try:
        res = await client.post("/vectors/tags", json={"tags": [str(tag) for tag in tags], "taskId": str(task_id), "userId": str(user_id)})
        logger.debug(f"Response status: {res.status_code}, Response: {res.text}")
        if res.status_code != 200:
            raise Exception(f"Save user tags failed with {res.status_code}")
    except Exception as e:
        raise Exception(f"Failed to save user tags") from e


async def delete_tags_by_task_id(task_id: uuid.UUID):
    try:
        res = await client.delete(f"/vectors/by-task/{task_id}")
        logger.debug(f"Response status: {res.status_code}, Response: {res.text}")
        if res.status_code != 200:
            raise Exception(f"Delete tags by task id failed with {res.status_code}")
    except Exception as e:
        raise Exception(f"Failed to delete tags by task id") from e


async def accept_recommendation(recommendation_id):
    try:
        res = await client.patch(f"/learning/{recommendation_id}/success")
        logger.debug(f"Response status: {res.status_code}, Response: {res.text}")
        if res.status_code != 200:
            raise Exception(f"Accept user recommendation failed with {res.status_code}")
    except Exception as e:
        raise Exception(f"Failed to accept user recommendation") from e


async def decline_recommendation(recommendation_id):
    try:
        res = await client.patch(f"/learning/{recommendation_id}/fail")
        logger.debug(f"Response status: {res.status_code}, Response: {res.text}")
        if res.status_code != 200:
            raise Exception(f"Decline user recommendation failed with {res.status_code}")
    except Exception as e:
        raise Exception(f"Failed to decline user recommendation") from e


def init_embedding():
    global client

    validate_env("EMBEDDINGS_PROCESSOR_KEY")
    validate_env("EMBEDDINGS_PROCESSOR_HOST")
    embedder_host = os.environ["EMBEDDINGS_PROCESSOR_HOST"]
    if embedder_host.endswith("/"):
        embedder_host = embedder_host[:-1]

    client = httpx.AsyncClient(base_url=embedder_host + "/api", headers={"Accept": "application/json", "Content-Type": "application/json", "X-API-KEY": os.environ["EMBEDDINGS_PROCESSOR_KEY"]}, timeout=timeout)


async def stop_embedding():
    await client.aclose()
