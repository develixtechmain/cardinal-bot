import asyncio
import logging
from typing import Any

from bot.notification.notification import Notification, NotificationType
from consts import UserChannelType
from service.channels import fetch_user_channels_by_user_id

logger = logging.getLogger(__name__)

notification_queue: asyncio.Queue = asyncio.Queue(maxsize=10000)


async def push_notification(user_id, notification_type: NotificationType):
    await push_notification_with_payload(user_id, notification_type, None)


async def push_notification_with_payload(user_id, notification_type: NotificationType, payload: dict[str, Any] | None):
    await push_raw_notification({"user_id": user_id, "type": notification_type, "chat_id": -1, "payload": payload})


async def push_raw_notification(notification: Notification):
    user_id = notification["user_id"]
    notification_type = notification["type"]
    payload = notification.get("payload") or {}
    notification["payload"] = payload
    payload["user_id"] = user_id

    must_core = payload.get("must_core", False)
    try:
        core_channel = await fetch_user_channels_by_user_id(user_id, UserChannelType.CORE)
        if core_channel:
            notification["chat_id"] = core_channel[0]["chat_id"]
            payload["chat"] = UserChannelType.CORE
            notification_queue.put_nowait(notification)
        else:
            if must_core:
                logger.warning(f"Sending {NotificationType.NO_CORE_CHANNEL} notification instead of {notification_type} to {user_id}")
                notification["type"] = NotificationType.NO_CORE_CHANNEL

            recommendations_channel = await fetch_user_channels_by_user_id(user_id, UserChannelType.RECOMMENDATION)
            if recommendations_channel:
                notification["chat_id"] = recommendations_channel[0]["chat_id"]
                payload["chat"] = UserChannelType.RECOMMENDATION
                notification_queue.put_nowait(notification)
            else:
                logger.error(f"Failed to notify user: no channels linked for user {user_id}")
    except Exception as e:
        print(f"Failed to send notification {notification_type} for {user_id}: {e}")
