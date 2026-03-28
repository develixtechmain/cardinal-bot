import asyncio
import json
import logging
import uuid
from typing import List

from asyncpg import UniqueViolationError
from fastapi import HTTPException

from bot.notification.notification import NotificationType
from bot.notification.queue import push_notification_with_payload
from external import embedding
from service.db import get_pool, get_task_stats, set_task_stats
from utils import data_to_update_query

logger = logging.getLogger(__name__)


async def fetch_user_tasks_stats(user_id: uuid.UUID):
    async with get_pool().acquire() as conn:
        query = """
            SELECT ut.id AS id, COALESCE(ROUND(AVG(ts.count)), 0) AS avg, COALESCE(SUM(ts.count), 0) AS total, 
            COALESCE(SUM(CASE WHEN ts.date = CURRENT_DATE THEN ts.count ELSE 0 END), 0) AS today
            FROM user_tasks ut
            LEFT JOIN task_statistics ts ON ut.id = ts.task_id
            WHERE ut.user_id = $1
            GROUP BY ut.id;
        """
        result = await conn.fetch(query, user_id)
        if result:
            stats = {}
            for task in result:
                stats[task["id"]] = {"today": task["today"], "avg": task["avg"], "total": task["total"]}
            return stats
        return {}


async def increment_stats(task_id):
    async with get_pool().acquire() as conn:
        try:
            exists = get_task_stats(task_id)
            if exists:
                result = await conn.execute("UPDATE task_statistics SET count = count + 1 WHERE task_id = $1 AND date = CURRENT_DATE", task_id)
                logger.info(f"Task {task_id} stat updated from cache")
            else:
                try:
                    result = await conn.execute("INSERT INTO task_statistics (task_id, date, count) VALUES ($1, CURRENT_DATE, 1)", task_id)
                    logger.info(f"Task {task_id} stat inserted without cache")
                except UniqueViolationError:
                    result = await conn.execute("UPDATE task_statistics SET count = count + 1 WHERE task_id = $1 AND date = CURRENT_DATE", task_id)
                    logger.info(f"Task {task_id} stat updated without cache")
            if result.startswith(("INSERT", "UPDATE")):
                if not exists:
                    set_task_stats(task_id)
            else:
                logger.warning(f"Unexpected result executing increment for {task_id}: {result}")
        except Exception as e:
            logger.warning(f"Failed to increment stats for {task_id}: {e}")


# TASKS
async def fetch_task_title_by_id(user_id: uuid.UUID, task_id: uuid.UUID):
    async with get_pool().acquire() as conn:
        result = await conn.fetchval("SELECT title FROM user_tasks WHERE user_id = $1 AND id = $2", user_id, task_id)
        if result:
            return result
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


async def fetch_tasks_by_user_id(user_id: uuid.UUID):
    async with get_pool().acquire() as conn:
        query = """
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
        """
        result = await conn.fetch(query, user_id)
        return result if result else []


async def save_user_task(user_id: uuid.UUID, title: str, cloud: List[str]):
    async with get_pool().acquire() as conn:
        async with conn.transaction():
            count = await conn.fetchval("SELECT COUNT(1) FROM user_tasks WHERE user_id = $1;", user_id)
            if count >= 5:
                raise HTTPException(status_code=409, detail="User reached tasks limit")

            result = await conn.fetchrow("INSERT INTO user_tasks (user_id, title, tags) VALUES ($1, $2, $3) RETURNING *;", user_id, title, json.dumps(cloud))
            if result:
                await embedding.save_tags(user_id, result["id"], cloud)
                if count == 0:
                    asyncio.create_task(push_notification_with_payload(user_id, NotificationType.BRIEFING_COMPLETED, {"must_core": True}))
                return result
        raise Exception("Failed to create user task")


async def patch_task_by_id(user_id: uuid.UUID, task_id: uuid.UUID, patch):
    async with get_pool().acquire() as conn:
        async with conn.transaction():
            task = await conn.fetchrow("SELECT * FROM user_tasks WHERE user_id = $1 AND id = $2 FOR UPDATE;", user_id, task_id)
            if task is None:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

            updates = {}
            if patch.title and task["title"] != patch.title:
                updates["title"] = patch.title

            if patch.active is not None and task["active"] != patch.active:
                updates["active"] = patch.active

            update_query, update_params = data_to_update_query(updates, 3)
            if not update_query or not update_params:
                return task

            if updates.get("active"):
                await embedding.save_tags(user_id, task_id, json.loads(task["tags"]))
            elif updates.get("active") is False:
                await embedding.delete_tags_by_task_id(task_id)

            result = await conn.fetchrow(f"UPDATE user_tasks SET {update_query} WHERE user_id = $1 AND id = $2 RETURNING *;", user_id, task_id, *update_params)
            if result:
                return result
    raise Exception("Failed to patch user task")


async def delete_task_by_id(user_id: uuid.UUID, task_id: uuid.UUID):
    async with get_pool().acquire() as conn:
        await embedding.delete_tags_by_task_id(task_id)

        result = await conn.execute("DELETE FROM user_tasks WHERE user_id = $1 AND id = $2;", user_id, task_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Task not found")
