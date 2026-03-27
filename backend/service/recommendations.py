import logging
import uuid

from service.db import get_pool

logger = logging.getLogger(__name__)


async def fetch_recommendation_by_id(recommendation_id: uuid.UUID):
    async with get_pool().acquire() as conn:
        result = await conn.fetchrow("SELECT * FROM user_recommendations WHERE id = $1;", recommendation_id)
        if result:
            return result
        else:
            raise Exception("Failed to find recommendation")


async def delete_user_recommendation(user_id: uuid.UUID, recommendation_id: uuid.UUID):
    async with get_pool().acquire() as conn:
        result = await conn.execute("DELETE FROM user_recommendations WHERE user_id = $1 AND id = $2;", user_id, recommendation_id)
        if result == "DELETE 0":
            logger.warning(f"User {user_id} recommendation not found for delete {recommendation_id}")
