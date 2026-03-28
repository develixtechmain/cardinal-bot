from bot.core import send_briefing_completed, send_purchase_done, send_purchase_failed, send_trial_ended, send_unsubscribed
from bot.notification.notification import NotificationType
from bot.notification.queue import notification_queue
from bot.recommendations import send_no_core_channel, send_unsubscribed_daily, send_unsubscribed_found
from service.notifications import delete_unsubscribed_notification, notification_send, verify_need_to_send

ALWAYS_SEND_HANDLERS = {
    NotificationType.PURCHASE_DONE: send_purchase_done,
    NotificationType.PURCHASE_FAILED: send_purchase_failed,
    NotificationType.NO_CORE_CHANNEL: send_no_core_channel,
    NotificationType.UNSUBSCRIBED_DAILY: send_unsubscribed_daily,
}

VERIFY_SEND_HANDLERS = {
    NotificationType.BRIEFING_COMPLETED: send_briefing_completed,
    NotificationType.TRIAL_ENDED: send_trial_ended,
    NotificationType.UNSUBSCRIBED: send_unsubscribed,
    NotificationType.UNSUBSCRIBED_FOUND: send_unsubscribed_found,
}

EXTRA_HANDLERS = {NotificationType.PURCHASE_DONE: delete_unsubscribed_notification}


async def notifier():
    while True:
        notification = await notification_queue.get()
        chat_id = notification["chat_id"]
        notification_type = notification["type"]
        payload = notification.get("payload", {})
        try:
            await notify(notification_type, chat_id, payload)
        except Exception as e:
            print(f"Failed to send notification {notification_type} in {chat_id}: {e}")
        finally:
            notification_queue.task_done()


async def notify(notification_type, chat_id, payload):
    if await handle(notification_type, chat_id, payload):
        if handler := EXTRA_HANDLERS.get(notification_type):
            await handler(chat_id, payload)


async def handle(notification_type, chat_id, payload) -> bool:
    if handler := ALWAYS_SEND_HANDLERS.get(notification_type):
        await handler(chat_id, payload)
        return True

    if handler := VERIFY_SEND_HANDLERS.get(notification_type):
        if await verify_need_to_send(notification_type, payload):
            await handler(chat_id, payload)
            await notification_send(notification_type, payload)
            return True

    return False
