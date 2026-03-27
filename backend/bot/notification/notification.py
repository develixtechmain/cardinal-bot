from enum import Enum
from typing import Any, TypedDict
from uuid import UUID


class NotificationType(str, Enum):
    PURCHASE_DONE = "purchase_done"
    PURCHASE_FAILED = "purchase_failed"
    BRIEFING_COMPLETED = "briefing_completed"
    NO_CORE_CHANNEL = "no_core_channel"
    TRIAL_ENDED = "trial_ended"
    UNSUBSCRIBED = "unsubscribed"
    UNSUBSCRIBED_FOUND = "unsubscribed_found"
    UNSUBSCRIBED_DAILY = "unsubscribed_daily"


class Notification(TypedDict):
    user_id: UUID
    chat_id: int
    type: NotificationType
    payload: dict[str, Any] | None
