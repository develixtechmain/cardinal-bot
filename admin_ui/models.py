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
