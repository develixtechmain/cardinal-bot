import json
import uuid
from typing import List

from cachetools import TTLCache
from fastapi import HTTPException

from db import get_pool

onboarding_cache = TTLCache(maxsize=100, ttl=1200)


async def fetch_user_tasks_stats(user_id: uuid.UUID):
    async with get_pool().acquire() as conn:
        result = await conn.fetch("""
            SELECT ut.id AS id, COALESCE(ROUND(AVG(ts.count)), 0) AS avg, COALESCE(SUM(ts.count), 0) AS total, 
            COALESCE(SUM(CASE WHEN ts.date = CURRENT_DATE THEN ts.count ELSE 0 END), 0) AS today
            FROM user_tasks ut
            LEFT JOIN task_statistics ts ON ut.id = ts.task_id
            WHERE ut.user_id = $1
            GROUP BY ut.id;
        """, user_id)
        if result:
            stats = {}
            for task in result:
                stats[task['id']] = {
                    'today': task['today'],
                    'avg': task['avg'],
                    'total': task['total']
                }
            return stats
        return {}


# TASKS
async def fetch_tasks_by_user_id(user_id: uuid.UUID):
    async with get_pool().acquire() as conn:
        result = await conn.fetch("""
            WITH stats AS (
                SELECT task_id, SUM(count) as total_count FROM task_statistics GROUP BY task_id
            ), today_stats AS (
                SELECT task_id, count as today_count FROM task_statistics WHERE date = CURRENT_DATE
            )
            SELECT 
                ut.*,
                COALESCE(stats.total_count, 0) as total_count,
                COALESCE(today_stats.today_count, 0) as today_count
            FROM user_tasks ut
            LEFT JOIN stats ON ut.id = stats.task_id
            LEFT JOIN today_stats ON ut.id = today_stats.task_id
            WHERE ut.user_id = $1;
        """, user_id)
        return result if result else []


async def save_user_task(user_id: uuid.UUID, cloud: List[str]):
    async with get_pool().acquire() as conn:
        result = await conn.fetchrow("INSERT INTO user_tasks (user_id, title, tags) VALUES ($1, $2, $3) RETURNING *", user_id, cloud[0], json.dumps(cloud))
        if result:
            return result
        raise Exception("Failed to create user task")


async def patch_task_by_id(user_id: uuid.UUID, task_id: uuid.UUID, active: bool):
    async with get_pool().acquire() as conn:
        async with conn.transaction():
            result = await conn.execute("UPDATE user_tasks SET active = $3 WHERE user_id = $1 AND id = $2 RETURNING *", user_id, task_id, active)
            if result:
                return result
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


async def delete_task_by_id(user_id: uuid.UUID, task_id: uuid.UUID):
    async with get_pool().acquire() as conn:
        result = await conn.execute("DELETE FROM user_tasks WHERE user_id = $1 AND id = $2", user_id, task_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Task not found")


# RECOMMENDATIONS
async def fetch_user_channels_by_user_id(user_id: uuid.UUID):
    async with get_pool().acquire() as conn:
        result = await conn.fetch("SELECT * FROM user_channels WHERE user_id = $1", user_id)
        if result:
            return result
        return []


async def save_user_channel(user_id: uuid.UUID, chat_id: int):
    async with get_pool().acquire() as conn:
        result = await conn.execute("INSERT INTO user_channels (user_id, chat_id) VALUES ($1, $2) ON CONFLICT (user_id, chat_id) DO NOTHING;", user_id, chat_id)
        rows_affected = result.split()[-1]
        return rows_affected == "1"


async def delete_user_channel(user_id: uuid.UUID, user_channel_id: uuid.UUID):
    async with get_pool().acquire() as conn:
        result = await conn.execute("DELETE FROM user_channels WHERE user_id = $1 AND id = $2", user_id, user_channel_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Channel not found")


# ONBOARDING
async def fetch_onboarding_by_id(onboarding_id: uuid.UUID, renew: bool = False):
    if not renew and onboarding_id in onboarding_cache:
        return onboarding_cache[onboarding_id]

    onboarding = await fetch_onboarding_from_db(onboarding_id)
    if onboarding:
        onboarding_cache[onboarding_id] = onboarding
        return onboarding
    raise HTTPException(status_code=404, detail=f"Onboarding {onboarding_id} not found")


async def fetch_onboarding_from_db(onboarding_id: uuid.UUID):
    async with get_pool().acquire() as conn:
        result = await conn.fetchrow("SELECT * FROM user_onboardings WHERE id = $1", onboarding_id)
        if result:
            return result
        return None


async def create_onboarding(user_id: uuid.UUID):
    async with get_pool().acquire() as conn:
        result = await conn.fetchrow("SELECT * FROM user_onboardings WHERE user_id = $1", user_id)
        if result:
            return result

        result = await conn.fetchrow("INSERT INTO user_onboardings (user_id) VALUES ($1) RETURNING *", user_id)
        if result:
            return result
        raise Exception("Failed to create onboarding")


async def update_onboarding_questions(onboarding_id: uuid.UUID, questions):
    await fetch_onboarding_by_id(onboarding_id)
    async with get_pool().acquire() as conn:
        await conn.execute("UPDATE user_onboardings SET questions = $2 WHERE id = $1", onboarding_id, json.dumps([{"question": key, "answer": value} for key, value in questions.items()]))
    onboarding_cache.pop(onboarding_id, None)


async def complete_onboarding(onboarding_id: uuid.UUID):
    async with get_pool().acquire() as conn:
        await conn.execute("UPDATE user_onboardings SET status = 'completed' WHERE id = $1", onboarding_id)
        onboarding_cache.pop(onboarding_id, None)


async def delete_onboarding_by_id(onboarding_id: uuid.UUID):
    async with get_pool().acquire() as conn:
        await conn.execute("DELETE FROM user_onboardings WHERE id = $1", onboarding_id)
        onboarding_cache.pop(onboarding_id, None)
