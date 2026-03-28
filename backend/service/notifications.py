import logging

from asyncpg import UniqueViolationError

from bot.notification.notification import NotificationType
from service.db import get_pool, get_user_notification_limits

# fmt: off
ONLY_ONCE_NOTIFICATIONS = (
    NotificationType.BRIEFING_COMPLETED,
    NotificationType.TRIAL_ENDED,
    NotificationType.UNSUBSCRIBED # Prolong deletes
)
# fmt: on
logger = logging.getLogger(__name__)


async def delete_unsubscribed_notification(_, payload):
    async with get_pool().acquire() as conn:
        await conn.execute("DELETE FROM user_notifications WHERE user_id = $1 AND notification_type = $2", payload["user_id"], NotificationType.UNSUBSCRIBED)


async def notification_send(notification_type: NotificationType, payload: dict):
    logger.info(f"notification_send notification {notification_type} for {payload}")
    if notification_type is NotificationType.TRIAL_ENDED or notification_type is NotificationType.UNSUBSCRIBED:
        subscription = payload["subscription"]
        await _mark_once(notification_type, subscription["user_id"])
    # TODO update


async def _mark_once(notification_type: NotificationType, user_id):
    async with get_pool().acquire() as conn:
        try:
            result = await conn.execute("INSERT INTO user_notifications (user_id, notification_type) VALUES ($1, $2)", user_id, notification_type)
        except UniqueViolationError:
            logger.warning(f"Notification {notification_type} is already send for {user_id}")
            return
        except Exception as e:
            logger.warning(f"Failed to mark notification {notification_type} send for {user_id}: {e}")
        if not result.startswith(("INSERT", "UPDATE")):
            logger.warning(f"Unexpected result marking {notification_type} send for {user_id}: {result}")


async def verify_need_to_send(notification_type: NotificationType, payload: dict) -> bool:
    user_id = payload["subscription"]["user_id"]
    log_payload = {k: v for k, v in payload.items() if k not in {"subscription"}}
    logger.info(f"verify_need_to_send notification {notification_type} for {user_id} with {log_payload}")
    if notification_type in ONLY_ONCE_NOTIFICATIONS:
        return await _verify_once(notification_type, user_id)
    elif notification_type is NotificationType.UNSUBSCRIBED_FOUND:
        return await _verify_day_total_less(notification_type, user_id, payload["date"], get_user_notification_limits(user_id))
    return False


async def _verify_once(notification_type, user_id):
    async with get_pool().acquire() as conn:
        result = await conn.fetchrow("SELECT * FROM user_notifications WHERE user_id = $1 AND notification_type = $2 LIMIT 1", user_id, notification_type)
        return True if not result else False


# fmt: off
async def _verify_day_total_less(notification_type, user_id, date, limit):
    async with get_pool().acquire() as conn:
        total =  await conn.fetchval("SELECT COALESCE(SUM(COALESCE((payload->'count')::int, 0)), 0) FROM user_notifications WHERE user_id = $1 AND notification_type = $2 AND date = $3", user_id, notification_type, date)
        logger.info(f"_verify_day_total_less returned {total <= limit} due to {total} <= {limit}")
        return total <= limit
# fmt: on


async def get_daily_totals():
    return None
