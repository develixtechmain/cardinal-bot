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


async def fetch_onboarding_by_id(onboarding_id: uuid.UUID, renew: bool = False):
    if not renew and onboarding_id in onboarding_cache:
        return onboarding_cache[onboarding_id]

    onboarding = await fetch_onboarding_from_db(onboarding_id)
    if onboarding:
        onboarding_cache[onboarding_id] = onboarding
        return onboarding
    raise HTTPException(status_code=404, detail=f"Onboarding {onboarding_id} not found")


async def fetch_onboarding_from_db(onboarding_id: uuid.UUID):
    async with pool.acquire() as conn:
        result = await conn.fetch("SELECT * FROM onboardings WHERE id = $1", onboarding_id)
        if result:
            return result[0]
        return None


async def create_onboarding(user_id):
    async with pool.acquire() as conn:
        result = await conn.fetch("SELECT * FROM onboardings WHERE user_id = $1", user_id)
        if result:
            return result[0]

        result = await conn.fetch("INSERT INTO onboardings (user_id) VALUES ($1) RETURNING *", user_id)
        if result:
            return result[0]
        raise Exception("Failed to create onboarding")


async def save_questions(onboarding_id, questions):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE onboardings SET questions = $2 WHERE id = $1", onboarding_id, json.dumps([{"question": key, "answer": value} for key, value in questions.items()]))
        onboarding_cache.pop(onboarding_id, None)


async def complete_onboarding(onboarding_id):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE onboardings SET status = 'completed' WHERE id = $1", onboarding_id)
        onboarding_cache.pop(onboarding_id, None)


async def delete_onboarding_by_id(onboarding_id):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM onboardings WHERE id = $1", onboarding_id)
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
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS onboardings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
                user_id UUID NOT NULL,
                questions JSONB NOT NULL DEFAULT '[]'::jsonb,
                status VARCHAR(11) NOT NULL DEFAULT 'uncompleted',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            )
        """)


async def disconnect():
    await pool.close()
    logger.info("PostgreSQL pool closed.")
