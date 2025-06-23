import asyncio
import os
import string
import uuid

import httpx

from utils import validate_env

embedder_search_url: string
embedder_confirm_url: string

good = 0
bad = 0
good_lock = asyncio.Lock()
bad_lock = asyncio.Lock()

headers: dict
timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=10)


async def search_candidates(message: string):
    global good, bad

    id = uuid.uuid4()
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(embedder_search_url, json={"message": message}, headers=headers, timeout=timeout)
            print(f"{id} Response status: {resp.status_code}, Response: {resp.text}")
            resp.raise_for_status()
            resp_data = resp.json()
            async with good_lock:
                good += 1
        except httpx.RequestError as e:
            async with bad_lock:
                bad += 1
                print(f"{id} Request error (e.g., timeout, network): {e}",
                      f"Good {good}, bad {bad}")
            resp_data = []
        except ValueError as e:
            async with bad_lock:
                bad += 1
                print(f"{id} JSON decode error: {e}",
                      f"Good {good}, bad {bad}")
            resp_data = []
        except Exception as e:
            async with bad_lock:
                bad += 1
                print(f"{id} Unexpected error: {e}, type: {type(e)}",
                      f"Good {good}, bad {bad}")
            resp_data = []
        return resp_data


async def confirm_recommendation(recommendation_id, selected_candidate):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(embedder_confirm_url, json={
                "recomendationId": str(recommendation_id),
                "submittedTaskId": selected_candidate['taskId'],
                "submittedVectors": [tag["id"] for tag in selected_candidate["tags"]]
            }, headers=headers, timeout=timeout)
            print(f"Response status: {resp.status_code}, Response: {resp.text}")
            resp.raise_for_status()
        except Exception as e:
            raise Exception(f"Failed to confirm recommendation: {e}")


def init_embedding():
    global embedder_search_url, embedder_confirm_url, headers

    validate_env("EMBEDDER_KEY")
    validate_env("EMBEDDER_HOST")
    embedder_search_url = os.environ["EMBEDDER_HOST"] + "/api/vectors/search"
    embedder_confirm_url = os.environ["EMBEDDER_HOST"] + "/api/recommendation/confirm"

    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": os.environ["EMBEDDER_KEY"],
    }
