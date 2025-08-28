import uuid

from cachetools import TTLCache
from fastapi import HTTPException

from db import get_pool

users_cache = TTLCache(maxsize=100, ttl=300)


async def create_user(tg_user, ref_id=None):
    user_id = tg_user['id']
    first_name = tg_user.get('first_name', 'Unknown')
    last_name = tg_user.get('last_name', 'Unknown')
    username = tg_user.get('username', 'Unknown')

    if first_name is None:
        first_name = 'Unknown'
    if last_name is None:
        last_name = 'Unknown'
    if username is None:
        username = 'Unknown'

    async with get_pool().acquire() as conn:
        result = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        if result:
            return result

        result = await conn.fetchrow("INSERT INTO users (user_id, first_name, last_name, username, referrer_id) VALUES ($1, $2, $3, $4, $5) RETURNING *", user_id, first_name, last_name, username,
                                     ref_id)
        if result:
            return result
        raise Exception("Failed to create onboarding")


async def fetch_user_by_id(user_id: uuid.UUID | int, from_tg: bool = False):
    if user_id in users_cache:
        return users_cache[user_id]

    user = await fetch_user_from_db(user_id, from_tg)
    if user:
        users_cache[user_id] = user
        return user
    raise HTTPException(status_code=404, detail=f"User {user_id} not found")


async def fetch_user_from_db(user_id: uuid.UUID, from_tg: bool = False):
    async with get_pool().acquire() as conn:
        if from_tg:
            result = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        else:
            result = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        if result:
            return result
        return None


async def patch_user_by_id(user_id: uuid.UUID, data):
    async with get_pool().acquire() as conn:
        async with conn.transaction():
            user_updates = data.model_dump(exclude_none=True)

            if not user_updates:
                return None

            update_fields = list(user_updates.keys())
            update_values = list(user_updates.values())

            updates = [f"{field} = ${i + 2}" for i, field in enumerate(update_fields)]
            update_query = f"UPDATE users SET {', '.join(updates)} WHERE id = $1 RETURNING *"

            values = [user_id] + update_values
            result = await conn.fetchrow(update_query, *values)
            if result:
                return result
        raise Exception("Failed to patch user")
