import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


def trace_enabled() -> bool:
    return bool(os.environ.get("TRACE_SERVICE_URL") and os.environ.get("TRACE_INGEST_KEY"))


async def _client_get() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(3.0, connect=2.0))
    return _client


async def emit(
    correlation_id: str,
    service: str,
    stage: str,
    status: str,
    detail: Optional[dict[str, Any]] = None,
    *,
    recommendation_id: Optional[UUID] = None,
    source_chat_id: Optional[str] = None,
    source_message_id: Optional[int] = None,
    duration_ms: Optional[int] = None,
) -> None:
    if not trace_enabled():
        return
    base = os.environ["TRACE_SERVICE_URL"].rstrip("/")
    key = os.environ["TRACE_INGEST_KEY"]
    body: dict[str, Any] = {
        "correlation_id": correlation_id,
        "service": service,
        "stage": stage,
        "status": status,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "detail": detail or {},
    }
    if recommendation_id is not None:
        body["recommendation_id"] = str(recommendation_id)
    if source_chat_id is not None:
        body["source_chat_id"] = source_chat_id
    if source_message_id is not None:
        body["source_message_id"] = source_message_id
    if duration_ms is not None:
        body["duration_ms"] = duration_ms
    try:
        c = await _client_get()
        r = await c.post(f"{base}/internal/traces/events", json=body, headers={"X-Trace-API-Key": key})
        r.raise_for_status()
    except Exception as e:
        logger.debug("trace emit failed: %s", e)
