import re
import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.I,
)


class TraceEventOut(BaseModel):
    id: int
    correlation_id: uuid.UUID
    occurred_at: datetime
    service: str
    stage: str
    status: str
    duration_ms: Optional[int]
    parent_event_id: Optional[int]
    detail: dict[str, Any]
    recommendation_id: Optional[uuid.UUID]
    otel_trace_id: Optional[str]
    otel_span_id: Optional[str]


class TraceRootOut(BaseModel):
    correlation_id: uuid.UUID
    source_chat_id: Optional[str]
    source_message_id: Optional[int]
    source_text: Optional[str] = None
    first_seen_at: datetime
    last_event_at: datetime
    last_summary: Optional[str]


class TraceDetailResponse(BaseModel):
    root: TraceRootOut
    events: list[TraceEventOut]
    summary: str


class TraceSearchItem(BaseModel):
    correlation_id: uuid.UUID
    source_chat_id: Optional[str]
    source_message_id: Optional[int]
    source_text: Optional[str] = None
    last_event_at: datetime
    last_summary: Optional[str]
    event_count: int


class TraceSearchResponse(BaseModel):
    items: list[TraceSearchItem]
    total: int


# ── User models ────────────────────────────────────────────────────────────

class UserListItem(BaseModel):
    id: uuid.UUID
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    created_at: datetime
    subscription_ends_at: Optional[datetime]
    trial_ends_at: Optional[datetime]
    leads_today: int = 0
    leads_month: int = 0


class UserListResponse(BaseModel):
    items: list[UserListItem]
    total: int


class TaskOut(BaseModel):
    id: uuid.UUID
    title: str
    tags: Any
    active: bool
    created_at: datetime


class UserDetailResponse(BaseModel):
    id: uuid.UUID
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    balance: int
    created_at: datetime
    subscription_ends_at: Optional[datetime]
    trial_ends_at: Optional[datetime]
    tasks: list[TaskOut] = []


class LeadItem(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    task_title: Optional[str] = None
    recommendation: dict[str, Any]
    accepted: Optional[bool]
    created_at: datetime


class LeadListResponse(BaseModel):
    items: list[LeadItem]
    total: int


class PaymentItem(BaseModel):
    id: uuid.UUID
    amount: int
    status: str
    payment: str
    recurrent: bool
    created_at: datetime
    payment_timestamp: Optional[datetime]


class PaymentListResponse(BaseModel):
    items: list[PaymentItem]
    total: int


class BalanceTopUpRequest(BaseModel):
    amount: int = Field(..., gt=0, le=1000000, description="Amount to add to user balance (max 1,000,000)")


class BalanceTopUpResponse(BaseModel):
    new_balance: int
    message: str
    notification_sent: bool = False


def parse_search_query(q: str) -> tuple[str, Any]:
    q = q.strip()
    if not q:
        return ("empty", None)
    if _UUID_RE.match(q):
        return ("correlation", q)
    if ":" in q:
        chat_part, msg_part = q.rsplit(":", 1)
        chat_part = chat_part.strip()
        msg_part = msg_part.strip()
        if chat_part and msg_part.isdigit():
            return ("source", (chat_part, int(msg_part)))
    return ("like", q)


def compute_summary_from_events(events: list[dict]) -> str:
    if not events:
        return "No events"
    errors = [e for e in events if e.get("status") == "error"]
    if errors:
        last = errors[-1]
        return f"Error at {last.get('service')}/{last.get('stage')}"
    stages = [f"{e.get('service')}/{e.get('stage')}" for e in events[-3:]]
    return " \u2192 ".join(stages)
