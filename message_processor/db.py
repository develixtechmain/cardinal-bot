import json
import logging
import os
import uuid

import asyncpg
from cachetools import LRUCache

from utils import validate_env

pool: asyncpg.pool.Pool
users_cache = LRUCache(maxsize=100)

logger = logging.getLogger(__name__)


async def fetch_user_by_id(user_id: uuid.UUID):
    if user_id in users_cache:
        return users_cache[user_id]

    user = await fetch_user_from_db(user_id)
    if user:
        users_cache[user_id] = user
        return user
    raise Exception(f"User {user_id} not found")


async def fetch_user_from_db(user_id: uuid.UUID):
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)


async def get_user_stats(user_id, cutoff):
    async with pool.acquire() as conn:
        query = """
            SELECT 
                COUNT(1) AS total_recommendations,
                COUNT(CASE WHEN created_at > $2 THEN 1 END) AS recent_recommendations,
                MAX(created_at) AS last_recommendation_at
            FROM user_recommendations WHERE user_id = $1
        """
        stats = await conn.fetchrow(query, user_id, cutoff)

    if stats:
        return stats
    else:
        return {"total_recommendations": 0, "recent_recommendations": 0, "last_recommendation_at": None}


async def save_message(message):
    chat_id = message["chat_id"]
    message_id = message["message_id"]

    try:
        async with pool.acquire() as conn:
            await conn.execute("INSERT INTO telegram_messages (message) VALUES $1", message)
            logger.info(f"Message {message_id} from {chat_id} saved.")
    except Exception as e:
        logger.warning(f"Failed to save message {message_id} from {chat_id}: {e}")


async def save_recommendation(user, task_id, message):
    async with pool.acquire() as conn:
        query = """
            INSERT INTO user_recommendations (user_id, task_id, recommendation)
            VALUES($1, $2, $3)
            RETURNING id;
        """
        return await conn.fetchval(query, user["id"], task_id, json.dumps(message))


async def init_postgresql():
    global pool

    validate_env("DB_PASS")

    password = os.environ["DB_PASS"]

    pool = await asyncpg.create_pool(
        user=os.environ.get("DB_USER", "cardinal"),
        password=password,
        database=os.environ.get("DB_NAME", "cardinal"),
        host=os.environ.get("DB_HOST", "postgresql"),
        port=int(os.environ.get("DB_PORT", 5432)),
        min_size=10,
        max_size=20,
    )

    async with pool.acquire() as conn:
        await conn.execute("SELECT 1")


async def disconnect():
    await pool.close()
    logger.info("PostgreSQL pool closed.")
