import uuid

from asyncpg import UniqueViolationError
from fastapi import HTTPException

from service import users_total
from service.db import get_pool, users_cache
from utils import data_to_update_query


async def create_user(tg_user, ref_id=None):
    user_id = tg_user["id"]
    first_name = tg_user.get("first_name", None)
    last_name = tg_user.get("last_name", None)
    username = tg_user.get("username", None)

    async with get_pool().acquire() as conn:
        try:
            result = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1;", user_id)
            if result:
                return result

            result = await conn.fetchrow("INSERT INTO users (user_id, first_name, last_name, username, referrer_id) VALUES ($1, $2, $3, $4, $5) RETURNING *;", user_id, first_name, last_name, username, ref_id)
            if result:
                users_total.inc()
                return result
        except UniqueViolationError:
            result = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1;", user_id)
            if result:
                return result
        raise HTTPException(status_code=500, detail="Failed to create user")


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
            result = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1;", user_id)
        else:
            result = await conn.fetchrow("SELECT * FROM users WHERE id = $1;", user_id)
        if result:
            return result
        return None


async def patch_user_by_id(user_id: uuid.UUID, data):
    update_query, update_params = data_to_update_query(data.model_dump(), 2)
    if not update_query or not update_params:
        return None
    async with get_pool().acquire() as conn:
        async with conn.transaction():
            update_query = f"UPDATE users SET {update_query}, updated_at = CURRENT_TIMESTAMP WHERE id = $1 RETURNING *;"
            result = await conn.fetchrow(update_query, user_id, *update_params)
            if result:
                return result
        raise Exception("Failed to patch user")
