import uuid

from db import get_pool


async def fetch_user_refs(user_id: uuid.UUID):
    async with get_pool().acquire() as conn:
        result = await conn.fetch("""
            SELECT id, username, avatar_url, (balance > 0) AS billed FROM users WHERE referrer_id = $1
        """, user_id)
        return result if result else []


async def fetch_user_refs_stats(user_id: uuid.UUID):
    async with get_pool().acquire() as conn:
        result = await conn.fetch("""
            SELECT id, username, (balance > 0) AS billed FROM users WHERE referrer_id = $1
        """, user_id)
        return result if result else []
