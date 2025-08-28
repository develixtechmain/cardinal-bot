import json
import logging
import os
import uuid

import asyncpg
from cachetools import LRUCache
from fastapi import HTTPException

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
        result = await conn.fetch("SELECT * FROM users WHERE id = $1", user_id)
        if result:
            return result[0]
        return None


async def fetch_onboarding_by_id(user_id: uuid.UUID, onboarding_id: uuid.UUID, renew: bool = False):
    cache_key = str(user_id) + str(onboarding_id)
    if not renew and cache_key in onboarding_cache:
        return onboarding_cache[cache_key]

    onboarding = await fetch_onboarding_from_db(user_id, onboarding_id)
    if onboarding:
        onboarding_cache[cache_key] = onboarding
        return onboarding
    raise HTTPException(status_code=404, detail=f"Onboarding {onboarding_id} not found")


async def fetch_onboarding_from_db(user_id: uuid.UUID, onboarding_id: uuid.UUID):
    async with pool.acquire() as conn:
        result = await conn.fetch("SELECT * FROM user_onboardings WHERE user_id = $1 AND id = $2", user_id, onboarding_id)
        if result:
            return result[0]
        return None


async def create_onboarding(user_id):
    async with pool.acquire() as conn:
        result = await conn.fetch("SELECT * FROM user_onboardings WHERE user_id = $1 AND status != 'completed'", user_id)
        if result:
            return result[0]

        result = await conn.fetch("INSERT INTO user_onboardings (user_id) VALUES ($1) RETURNING *", user_id)
        if result:
            return result[0]
        raise Exception("Failed to create onboarding")


async def save_questions(user_id: uuid.UUID, onboarding_id: uuid.UUID, questions):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE user_onboardings SET questions = $3 WHERE user_id = $1 AND id = $2", user_id, onboarding_id,
                           json.dumps([{"question": key, "answer": value} for key, value in questions.items()]))
        onboarding_cache.pop(onboarding_id, None)


async def complete_onboarding(user_id: uuid.UUID, onboarding_id: uuid.UUID):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE user_onboardings SET status = 'completed' WHERE user_id = $1 AND id = $2", user_id, onboarding_id)
        onboarding_cache.pop(onboarding_id, None)


async def delete_onboarding_by_id(user_id: uuid.UUID, onboarding_id: uuid.UUID):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM user_onboardings WHERE user_id = $1 AND id = $2", user_id, onboarding_id)
        onboarding_cache.pop(onboarding_id, None)


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
        max_size=20
    )

    async with pool.acquire() as conn:
        await conn.execute("SELECT 1")


async def disconnect():
    await pool.close()
    logger.info("PostgreSQL pool closed.")
