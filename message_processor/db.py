import json
import logging
import os
import uuid

import asyncpg
import clickhouse_driver
from cachetools import LRUCache
from clickhouse_driver import Client
from dateutil.parser import isoparse

from utils import validate_env

click: clickhouse_driver.Client
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
        result = await conn.fetch("SELECT * FROM users WHERE id = $1", user_id)
        if result:
            return result[0]
        return None


async def get_user_stats(user_id, cutoff):
    async with pool.acquire() as conn:
        stats = await conn.fetch("""
            SELECT 
                COUNT(1) AS total_recommendations,
                COUNT(CASE WHEN created_at > $2 THEN 1 END) AS recent_recommendations,
                MAX(created_at) AS last_recommendation_at
            FROM recommendations WHERE user_id = $1
        """, user_id, cutoff)

    if stats:
        return stats[0]
    else:
        return {
            "total_recommendations": 0,
            "recent_recommendations": 0,
            "last_recommendation_at": None
        }


async def fetch_user_task(task_id):
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT title, tags FROM user_tasks WHERE id = $1", task_id
        )
        if result:
            return result
        return None


async def save_in_clickhouse(message):
    chat_id = str(message['chat_id'])
    user_id = str(message['user_id'])
    message_id = message['message_id']
    created_at = isoparse(message['created_at'])

    click_data = [
        [
            chat_id, str(message['chat_title']), str(message['chat_username']),
            user_id, str(message['user_username']), str(message['user_firstname']), str(message['user_lastname']),
            int(message_id), str(message["text"]), created_at
        ]
    ]
    try:
        click.execute("""
            INSERT INTO telegram_messages 
            (chat_id, chat_title, chat_username, 
            user_id, user_username, user_firstname, user_lastname, 
            message_id, text, created_at)
            VALUES
        """, click_data)
        logger.info(f"Message {message_id} from {chat_id} saved to ClickHouse")
    except Exception as e:
        logger.warning(f"Failed to save message {message_id} from {chat_id} to ClickHouse: {e}")
    return chat_id, message_id


async def save_recommendation(user, task_id, recommendation):
    async with pool.acquire() as conn:
        query = """
            INSERT INTO user_recommendations (user_id, task_id, recommendation)
            VALUES($1, $2, $3)
            RETURNING id;
        """
        return await conn.fetchval(query, user['id'], task_id, json.dumps(recommendation))


async def init_click():
    global click

    validate_env("CLICKHOUSE_PASS")

    password = os.environ["CLICKHOUSE_PASS"]

    click = Client(
        host=os.environ.get("CLICKHOUSE_HOST", "clickhouse"),
        database=os.environ.get("CLICKHOUSE_DATABASE", "cardinal"),
        user=os.environ.get("CLICKHOUSE_USER", "cardinal"),
        password=password,
    )
    click.execute("""
    CREATE TABLE IF NOT EXISTS telegram_messages (
        chat_id String,
        chat_title String,
        chat_username String,
        user_id String,
        user_username String,
        user_firstname String,
        user_lastname String,
        message_id UInt64,
        text String,
        created_at DateTime
    ) ENGINE = MergeTree()
    ORDER BY (chat_id, message_id)
    """)


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
    await click.disconnect()
    logger.info("ClickHouse connection closed.")
    await pool.close()
    logger.info("PostgreSQL pool closed.")
