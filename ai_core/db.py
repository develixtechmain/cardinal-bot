import json
import logging
import os
import uuid
from typing import Literal

import asyncpg
from cachetools import LRUCache
from fastapi import HTTPException

from metrics import onboardings_total
from utils import validate_env

pool: asyncpg.pool.Pool
users_cache = LRUCache(maxsize=100)
onboarding_cache = LRUCache(maxsize=100)

logger = logging.getLogger(__name__)


async def fetch_user_by_id(user_id: uuid.UUID):
    if user_id in users_cache:
        return users_cache[user_id]

    user = await fetch_user_from_db(user_id)
    if user:
        users_cache[user_id] = user
        return user
    raise HTTPException(status_code=404, detail=f"User {user_id} not found")


async def fetch_user_from_db(user_id: uuid.UUID):
    async with pool.acquire() as conn:
        result = await conn.fetch("SELECT * FROM users WHERE id = $1;", user_id)
        if result:
            return result[0]
        return None


async def fetch_onboarding_by_id(user_id: uuid.UUID, onboarding_id: uuid.UUID, renew: bool = False):
    key = cache_key(user_id, onboarding_id)
    if not renew and key in onboarding_cache:
        return onboarding_cache[key]

    onboarding = await fetch_onboarding_from_db(user_id, onboarding_id)
    if onboarding:
        onboarding_cache[key] = onboarding
        return onboarding
    raise HTTPException(status_code=404, detail=f"Onboarding {onboarding_id} not found")


async def fetch_onboarding_from_db(user_id: uuid.UUID, onboarding_id: uuid.UUID):
    async with pool.acquire() as conn:
        result = await conn.fetchrow("SELECT * FROM user_onboardings WHERE user_id = $1 AND id = $2;", user_id, onboarding_id)
        if result:
            return result
        return None


async def create_onboarding(user_id):
    async with pool.acquire() as conn:
        result = await conn.fetch("SELECT * FROM user_onboardings WHERE user_id = $1 AND status != 'completed';", user_id)
        if result:
            return result[0]

        result = await conn.fetchrow("INSERT INTO user_onboardings (user_id) VALUES ($1) RETURNING *;", user_id)
        if result:
            onboardings_total.inc()
            return result
        raise Exception("Failed to create onboarding")


async def save_questions(user_id: uuid.UUID, onboarding_id: uuid.UUID, questions):
    async with pool.acquire() as conn:
        query = """
            UPDATE user_onboardings SET 
                questions = $3,
                answers = answers + 1,
                status = CASE WHEN (answers + 1) >= 3 THEN 'completed' ELSE status END
            WHERE user_id = $1 AND id = $2 RETURNING *;
        """

        result = await conn.fetchrow(query, user_id, onboarding_id, json.dumps(questions))

        if result:
            onboarding_cache[cache_key(user_id, onboarding_id)] = result
            return result

        raise Exception("Failed to save onboarding questions")


async def complete_onboarding(user_id: uuid.UUID, onboarding_id: uuid.UUID):
    async with pool.acquire() as conn:
        result = await conn.fetchrow("UPDATE user_onboardings SET status = 'completed' WHERE user_id = $1 AND id = $2 RETURNING *;", user_id, onboarding_id)
        if result:
            onboarding_cache[cache_key(user_id, onboarding_id)] = result
            return result
        raise Exception("Failed to complete onboarding")


async def restart_onboarding(user_id: uuid.UUID, onboarding_id: uuid.UUID):
    async with pool.acquire() as conn:
        result = await conn.fetchrow("UPDATE user_onboardings SET answers = 0, status = 'uncompleted' WHERE user_id = $1 AND id = $2 RETURNING *;", user_id, onboarding_id)
        if result:
            onboarding_cache[cache_key(user_id, onboarding_id)] = result
            return result
        raise Exception("Failed to complete onboarding")


async def delete_onboarding_by_id(user_id: uuid.UUID, onboarding_id: uuid.UUID):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM user_onboardings WHERE user_id = $1 AND id = $2;", user_id, onboarding_id)
        onboarding_cache.pop(cache_key(user_id, onboarding_id), None)


def cache_key(user_id: uuid.UUID, onboarding_id: uuid.UUID):
    return str(user_id) + str(onboarding_id)


async def init_postgresql():
    global pool

    validate_env("DB_PASS")

    password = os.environ["DB_PASS"]

    pool = await asyncpg.create_pool(
        user=os.environ.get("DB_USER", "cardinal"),
        password=password,
        database=os.environ.get("DB_NAME", "cardinal"),
        host=os.environ.get("DB_HOST", "postgresql"),
        port=os.environ.get("DB_PORT", 5432),
        min_size=10,
        max_size=20,
    )

    async with pool.acquire() as conn:
        await conn.execute("SELECT 1")


async def disconnect():
    await pool.close()
    logger.info("PostgreSQL pool closed.")
