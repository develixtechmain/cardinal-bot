import logging
import os

import httpx

from utils import validate_env

client: httpx.AsyncClient

logger = logging.getLogger(__name__)


async def search_candidates(message: str):
    try:
        resp = await client.post("/vectors/search", json={"message": message})
        resp.raise_for_status()
        resp_data = resp.json()
    except Exception as e:
        logger.warning(f"Failed to search for candidates: {e}")
        resp_data = []
    logger.debug(f"Found {len(resp_data)} candidates")
    return resp_data


async def confirm_recommendation(recommendation_id, selected_candidate):
    try:
        resp = await client.post("/recommendation/confirm", json={"recommendationId": str(recommendation_id), "taskId": str(selected_candidate["taskId"])})
        resp.raise_for_status()
    except Exception as e:
        raise Exception(f"Failed to confirm recommendation") from e


def init_embedding():
    global client

    validate_env("EMBEDDINGS_PROCESSOR_KEY")
    validate_env("EMBEDDINGS_PROCESSOR_HOST")

    client = httpx.AsyncClient(
        base_url=os.environ["EMBEDDINGS_PROCESSOR_HOST"] + "/api",
        headers={"Content-Type": "application/json", "X-API-KEY": os.environ["EMBEDDINGS_PROCESSOR_KEY"]},
        timeout=httpx.Timeout(connect=60.0, read=60.0, write=60.0, pool=10),
    )
