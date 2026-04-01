import logging
import uuid

from consts import UserChannelType
from service.db import get_pool

logger = logging.getLogger(__name__)


async def fetch_user_channels_by_user_id(user_id: uuid.UUID, channel_type: UserChannelType):
    async with get_pool().acquire() as conn:
        result = await conn.fetch("SELECT * FROM user_channels WHERE user_id = $1 AND channel_type = $2 AND active = true;", user_id, channel_type)
        if result:
            return result
        return []


async def deactivate_channel(chat_id: int):
    async with get_pool().acquire() as conn:
        await conn.execute("UPDATE user_channels SET active = false WHERE chat_id = $1;", chat_id)
    logger.info(f"Deactivated channel chat_id={chat_id}")


async def verify_user_channel(user_id: uuid.UUID, chat_id: int, channel_type: UserChannelType):
    logger.info(f"verify_user_channel user_id {user_id}, chat_id {chat_id}, channel_type {channel_type}")
    async with get_pool().acquire() as conn:
        async with conn.transaction():
            result = await conn.fetchrow("SELECT * FROM user_channels WHERE user_id = $1 AND channel_type = $2 FOR UPDATE;", user_id, channel_type)
            if not result:
                result = await conn.fetchrow(
                    "INSERT INTO user_channels (user_id, chat_id, channel_type) VALUES ($1, $2, $3) ON CONFLICT (user_id, chat_id, channel_type) DO NOTHING RETURNING *;", user_id, chat_id, channel_type
                )
            elif result["chat_id"] != chat_id or not result["active"]:
                result = await conn.fetchrow(f"UPDATE user_channels SET chat_id = $2, active = true WHERE id = $1 RETURNING *;", result["id"], chat_id)
            if not result or result["chat_id"] != chat_id:
                logger.warning(f"Failed to verify user {user_id} channel {chat_id} for {channel_type}")
            return result
