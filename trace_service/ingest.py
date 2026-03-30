import json
import logging
from datetime import datetime, timezone

import asyncpg

from models import TraceEventIngest, compute_summary_from_events

logger = logging.getLogger(__name__)


async def ingest_event(conn: asyncpg.Connection, body: TraceEventIngest) -> int:
    occurred = body.occurred_at or datetime.now(timezone.utc)
    chat_id = body.source_chat_id
    msg_id = body.source_message_id
    if chat_id is None and body.detail:
        chat_id = body.detail.get("chat_id") or body.detail.get("source_chat_id")
    if msg_id is None and body.detail:
        mid = body.detail.get("message_id")
        if mid is not None:
            try:
                msg_id = int(mid)
            except (TypeError, ValueError):
                pass

    await conn.execute(
        """
        INSERT INTO message_trace_roots (correlation_id, source_chat_id, source_message_id, first_seen_at, last_event_at, last_summary)
        VALUES ($1, $2, $3, $4, $4, $5)
        ON CONFLICT (correlation_id) DO UPDATE SET
            last_event_at = GREATEST(message_trace_roots.last_event_at, EXCLUDED.last_event_at),
            source_chat_id = COALESCE(message_trace_roots.source_chat_id, EXCLUDED.source_chat_id),
            source_message_id = COALESCE(message_trace_roots.source_message_id, EXCLUDED.source_message_id),
            last_summary = EXCLUDED.last_summary
        """,
        body.correlation_id,
        str(chat_id) if chat_id is not None else None,
        msg_id,
        occurred,
        f"{body.service}/{body.stage}",
    )

    event_id = await conn.fetchval(
        """
        INSERT INTO message_trace_events (
            correlation_id, occurred_at, service, stage, status, duration_ms,
            parent_event_id, detail, recommendation_id, otel_trace_id, otel_span_id
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9, $10, $11)
        RETURNING id
        """,
        body.correlation_id,
        occurred,
        body.service,
        body.stage,
        body.status,
        body.duration_ms,
        body.parent_event_id,
        json.dumps(body.detail),
        body.recommendation_id,
        body.otel_trace_id,
        body.otel_span_id,
    )

    rows = await conn.fetch(
        """
        SELECT service, stage, status FROM message_trace_events
        WHERE correlation_id = $1 ORDER BY occurred_at ASC, id ASC
        """,
        body.correlation_id,
    )
    events_dicts = [dict(r) for r in rows]
    summary = compute_summary_from_events(events_dicts)
    await conn.execute(
        "UPDATE message_trace_roots SET last_summary = $2, last_event_at = $3 WHERE correlation_id = $1",
        body.correlation_id,
        summary,
        occurred,
    )
    return int(event_id)


async def ingest_event_pool(pool: asyncpg.Pool, body: TraceEventIngest) -> int:
    async with pool.acquire() as conn:
        async with conn.transaction():
            return await ingest_event(conn, body)
