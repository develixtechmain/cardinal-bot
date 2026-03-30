import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import asyncpg
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import trace_api_key
from db import close_db, get_pool, init_db
from ingest import ingest_event_pool
from models import (
    TraceDetailResponse,
    TraceEventIngest,
    TraceEventOut,
    TraceRootOut,
    TraceSearchItem,
    TraceSearchResponse,
    compute_summary_from_events,
    parse_search_query,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def verify_trace_api_key(request: Request) -> None:
    expected = trace_api_key()
    if not expected:
        raise HTTPException(status_code=503, detail="TRACE_SERVICE_API_KEY is not configured")
    header = request.headers.get("X-Trace-API-Key") or request.headers.get("x-trace-api-key")
    if header != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Trace-API-Key")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(title="Cardinal Message Trace Service", lifespan=lifespan, redirect_slashes=False)

_ui_dir = Path(__file__).resolve().parent / "ui"
if _ui_dir.is_dir():
    app.mount("/ui", StaticFiles(directory=str(_ui_dir), html=True), name="ui")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/internal/traces/events", dependencies=[Depends(verify_trace_api_key)])
async def post_event(body: TraceEventIngest):
    pool = get_pool()
    try:
        event_id = await ingest_event_pool(pool, body)
    except asyncpg.ForeignKeyViolationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parent_event_id or correlation: {e}") from e
    except Exception as e:
        logger.exception("ingest failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"id": event_id, "correlation_id": str(body.correlation_id)}


@app.get("/internal/traces", dependencies=[Depends(verify_trace_api_key)])
async def search_traces(
    q: str = Query("", description="correlation UUID, chat_id:message_id, or substring"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    pool = get_pool()
    kind, value = parse_search_query(q)
    async with pool.acquire() as conn:
        if kind == "empty":
            rows = await conn.fetch(
                """
                SELECT r.correlation_id, r.source_chat_id, r.source_message_id, r.last_event_at, r.last_summary,
                       (SELECT COUNT(*)::int FROM message_trace_events e WHERE e.correlation_id = r.correlation_id) AS event_count
                FROM message_trace_roots r
                ORDER BY r.last_event_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
            total = await conn.fetchval("SELECT COUNT(*)::int FROM message_trace_roots")
        elif kind == "correlation":
            cid = uuid.UUID(value)
            rows = await conn.fetch(
                """
                SELECT r.correlation_id, r.source_chat_id, r.source_message_id, r.last_event_at, r.last_summary,
                       (SELECT COUNT(*)::int FROM message_trace_events e WHERE e.correlation_id = r.correlation_id) AS event_count
                FROM message_trace_roots r
                WHERE r.correlation_id = $1
                LIMIT $2 OFFSET $3
                """,
                cid,
                limit,
                offset,
            )
            total = await conn.fetchval("SELECT COUNT(*)::int FROM message_trace_roots WHERE correlation_id = $1", cid)
        elif kind == "source":
            chat_id, msg_id = value
            rows = await conn.fetch(
                """
                SELECT r.correlation_id, r.source_chat_id, r.source_message_id, r.last_event_at, r.last_summary,
                       (SELECT COUNT(*)::int FROM message_trace_events e WHERE e.correlation_id = r.correlation_id) AS event_count
                FROM message_trace_roots r
                WHERE r.source_chat_id = $1 AND r.source_message_id = $2
                ORDER BY r.last_event_at DESC
                LIMIT $3 OFFSET $4
                """,
                chat_id,
                msg_id,
                limit,
                offset,
            )
            total = await conn.fetchval(
                "SELECT COUNT(*)::int FROM message_trace_roots WHERE source_chat_id = $1 AND source_message_id = $2",
                chat_id,
                msg_id,
            )
        else:
            pattern = f"%{value}%"
            rows = await conn.fetch(
                """
                SELECT r.correlation_id, r.source_chat_id, r.source_message_id, r.last_event_at, r.last_summary,
                       (SELECT COUNT(*)::int FROM message_trace_events e WHERE e.correlation_id = r.correlation_id) AS event_count
                FROM message_trace_roots r
                WHERE r.last_summary ILIKE $1 OR r.correlation_id::text ILIKE $1
                ORDER BY r.last_event_at DESC
                LIMIT $2 OFFSET $3
                """,
                pattern,
                limit,
                offset,
            )
            total = await conn.fetchval(
                "SELECT COUNT(*)::int FROM message_trace_roots WHERE last_summary ILIKE $1 OR correlation_id::text ILIKE $1",
                pattern,
            )

    items = [
        TraceSearchItem(
            correlation_id=r["correlation_id"],
            source_chat_id=r["source_chat_id"],
            source_message_id=r["source_message_id"],
            last_event_at=r["last_event_at"],
            last_summary=r["last_summary"],
            event_count=r["event_count"],
        )
        for r in rows
    ]
    return TraceSearchResponse(items=items, total=total or 0)


@app.get("/internal/traces/by-recommendation/{recommendation_id}", dependencies=[Depends(verify_trace_api_key)])
async def trace_by_recommendation(recommendation_id: uuid.UUID):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT correlation_id FROM message_trace_events WHERE recommendation_id = $1 ORDER BY id DESC LIMIT 1",
            recommendation_id,
        )
    if not row:
        raise HTTPException(status_code=404, detail="No trace for this recommendation_id")
    return {"correlation_id": str(row["correlation_id"])}


@app.get("/internal/traces/{correlation_id}", dependencies=[Depends(verify_trace_api_key)])
async def get_trace(correlation_id: uuid.UUID):
    pool = get_pool()
    async with pool.acquire() as conn:
        root = await conn.fetchrow("SELECT * FROM message_trace_roots WHERE correlation_id = $1", correlation_id)
        if not root:
            raise HTTPException(status_code=404, detail="Trace not found")
        ev_rows = await conn.fetch(
            """
            SELECT id, correlation_id, occurred_at, service, stage, status, duration_ms,
                   parent_event_id, detail, recommendation_id, otel_trace_id, otel_span_id
            FROM message_trace_events
            WHERE correlation_id = $1
            ORDER BY occurred_at ASC, id ASC
            """,
            correlation_id,
        )

    events_out = []
    for r in ev_rows:
        detail = r["detail"]
        if hasattr(detail, "keys"):
            detail = dict(detail)
        events_out.append(
            TraceEventOut(
                id=r["id"],
                correlation_id=r["correlation_id"],
                occurred_at=r["occurred_at"],
                service=r["service"],
                stage=r["stage"],
                status=r["status"],
                duration_ms=r["duration_ms"],
                parent_event_id=r["parent_event_id"],
                detail=detail or {},
                recommendation_id=r["recommendation_id"],
                otel_trace_id=r["otel_trace_id"],
                otel_span_id=r["otel_span_id"],
            )
        )
    root_out = TraceRootOut(
        correlation_id=root["correlation_id"],
        source_chat_id=root["source_chat_id"],
        source_message_id=root["source_message_id"],
        first_seen_at=root["first_seen_at"],
        last_event_at=root["last_event_at"],
        last_summary=root["last_summary"],
    )
    summary = compute_summary_from_events([e.model_dump() for e in events_out])
    return TraceDetailResponse(root=root_out, events=events_out, summary=summary)


@app.get("/internal/traces/{correlation_id}/summary", dependencies=[Depends(verify_trace_api_key)])
async def get_trace_summary(correlation_id: uuid.UUID):
    pool = get_pool()
    async with pool.acquire() as conn:
        root = await conn.fetchrow("SELECT * FROM message_trace_roots WHERE correlation_id = $1", correlation_id)
        if not root:
            raise HTTPException(status_code=404, detail="Trace not found")
        ev_rows = await conn.fetch(
            "SELECT service, stage, status FROM message_trace_events WHERE correlation_id = $1 ORDER BY occurred_at ASC, id ASC",
            correlation_id,
        )
    events_dicts = [dict(r) for r in ev_rows]
    return {
        "correlation_id": str(correlation_id),
        "summary": compute_summary_from_events(events_dicts),
        "event_count": len(events_dicts),
        "last_event_at": root["last_event_at"].isoformat(),
        "source_chat_id": root["source_chat_id"],
        "source_message_id": root["source_message_id"],
    }


@app.get("/")
async def root():
    if _ui_dir.is_dir():
        return FileResponse(_ui_dir / "index.html")
    return JSONResponse({"service": "trace-service", "docs": "/docs", "ui": "/ui/"})


def main():
    port = int(os.environ.get("PORT", "8010"))
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
