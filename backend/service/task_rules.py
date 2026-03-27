import itertools
import uuid

from service.db import get_pool, rules_cache


async def save_user_rules(user_id: uuid.UUID, task_id: uuid.UUID, rules: list[str]):
    async with get_pool().acquire() as conn:
        result = await conn.fetchrow("INSERT INTO user_task_rules (user_id, task_id, rules) VALUES ($1, $2, $3) RETURNING id;", user_id, task_id, rules)
        if result:
            rules_cache.pop(f"{user_id}_{task_id}", None)
        else:
            raise Exception("Failed to create task_rules")


async def fetch_user_rules(user_id: uuid.UUID, task_id: uuid.UUID):
    key = f"{user_id}_{task_id}"
    if key in rules_cache:
        return rules_cache[key]

    rules = await fetch_user_rules_from_db(user_id, task_id)
    rules_cache[key] = rules
    return rules


async def fetch_user_rules_from_db(user_id: uuid.UUID, task_id: uuid.UUID):
    async with get_pool().acquire() as conn:
        result = await conn.fetch("SELECT rules FROM user_task_rules WHERE user_id = $1 AND task_id = $2;", user_id, task_id)
        if result:
            return list(itertools.chain.from_iterable(row["rules"] for row in result))
        else:
            return None
