import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import httpx

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from auth import LoginRequest, LoginResponse, create_token, verify_token
from config import bot_token
from db import close_db, get_pool, get_main_pool, init_db
from models import (
    TraceDetailResponse,
    TraceEventOut,
    TraceRootOut,
    TraceSearchItem,
    TraceSearchResponse,
    compute_summary_from_events,
    parse_search_query,
    UserListResponse,
    UserListItem,
    UserDetailResponse,
    TaskOut,
    LeadListResponse,
    LeadItem,
    PaymentListResponse,
    PaymentItem,
    BalanceTopUpRequest,
    BalanceTopUpResponse,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(title="Cardinal Admin UI", lifespan=lifespan, redirect_slashes=False)

_ui_dir = Path(__file__).resolve().parent / "ui"
if _ui_dir.is_dir():
    app.mount("/ui", StaticFiles(directory=str(_ui_dir), html=True), name="ui")


# ── Auth ────────────────────────────────────────────────────────────────────

@app.post("/api/auth/login")
async def login(body: LoginRequest, response: Response):
    import time as _time
    from config import admin_login, admin_password
    if body.login != admin_login() or body.password != admin_password() or not admin_password():
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token, expires = create_token(body.login)
    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        samesite="strict",
        max_age=int((expires.timestamp() - _time.time())),
    )
    return LoginResponse(token=token, expires_at=expires.isoformat())


@app.post("/api/auth/logout")
async def logout(response: Response):
    response.delete_cookie("admin_token")
    return {"ok": True}


@app.get("/api/auth/me", dependencies=[Depends(verify_token)])
async def me(user: str = Depends(verify_token)):
    return {"login": user}


# ── Health ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


# ── Trace read endpoints (all require admin auth) ──────────────────────────

@app.get("/api/traces", dependencies=[Depends(verify_token)])
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
                SELECT r.correlation_id, r.source_chat_id, r.source_message_id, r.source_text,
                       r.last_event_at, r.last_summary,
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
                SELECT r.correlation_id, r.source_chat_id, r.source_message_id, r.source_text,
                       r.last_event_at, r.last_summary,
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
                SELECT r.correlation_id, r.source_chat_id, r.source_message_id, r.source_text,
                       r.last_event_at, r.last_summary,
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
                SELECT r.correlation_id, r.source_chat_id, r.source_message_id, r.source_text,
                       r.last_event_at, r.last_summary,
                       (SELECT COUNT(*)::int FROM message_trace_events e WHERE e.correlation_id = r.correlation_id) AS event_count
                FROM message_trace_roots r
                WHERE r.last_summary ILIKE $1 OR r.correlation_id::text ILIKE $1 OR r.source_text ILIKE $1
                ORDER BY r.last_event_at DESC
                LIMIT $2 OFFSET $3
                """,
                pattern,
                limit,
                offset,
            )
            total = await conn.fetchval(
                "SELECT COUNT(*)::int FROM message_trace_roots WHERE last_summary ILIKE $1 OR correlation_id::text ILIKE $1 OR source_text ILIKE $1",
                pattern,
            )

    items = [
        TraceSearchItem(
            correlation_id=r["correlation_id"],
            source_chat_id=r["source_chat_id"],
            source_message_id=r["source_message_id"],
            source_text=r["source_text"],
            last_event_at=r["last_event_at"],
            last_summary=r["last_summary"],
            event_count=r["event_count"],
        )
        for r in rows
    ]
    return TraceSearchResponse(items=items, total=total or 0)


@app.get("/api/traces/by-recommendation/{recommendation_id}", dependencies=[Depends(verify_token)])
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


@app.get("/api/traces/{correlation_id}", dependencies=[Depends(verify_token)])
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
        if isinstance(detail, str):
            detail = json.loads(detail)
        elif hasattr(detail, "keys"):
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
        source_text=root.get("source_text"),
        first_seen_at=root["first_seen_at"],
        last_event_at=root["last_event_at"],
        last_summary=root["last_summary"],
    )
    summary = compute_summary_from_events([e.model_dump() for e in events_out])
    return TraceDetailResponse(root=root_out, events=events_out, summary=summary)


@app.get("/api/traces/{correlation_id}/summary", dependencies=[Depends(verify_token)])
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


# ── User endpoints (main DB) ──────────────────────────────────────────────

@app.get("/api/users", dependencies=[Depends(verify_token)])
async def list_users(
    q: str = Query("", description="Search by user_id, username, first_name, last_name"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    mpool = get_main_pool()
    async with mpool.acquire() as conn:
        if q.strip():
            escaped_q = q.strip().replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{escaped_q}%"
            # Try numeric search for user_id too
            numeric_id = None
            try:
                numeric_id = int(q.strip())
            except ValueError:
                pass

            if numeric_id is not None:
                rows = await conn.fetch(
                    """
                    SELECT u.*, us.subscription_ends_at,
                           COALESCE((SELECT SUM(ts.count) FROM task_statistics ts
                                     JOIN user_tasks ut ON ut.id = ts.task_id
                                     WHERE ut.user_id = u.id AND ts.date = CURRENT_DATE), 0) AS leads_today,
                           COALESCE((SELECT SUM(ts.count) FROM task_statistics ts
                                     JOIN user_tasks ut ON ut.id = ts.task_id
                                     WHERE ut.user_id = u.id AND ts.date >= date_trunc('month', CURRENT_DATE)), 0) AS leads_month
                    FROM users u
                    LEFT JOIN user_subscriptions us ON us.user_id = u.id
                    WHERE u.user_id = $1
                       OR u.username ILIKE $2
                       OR u.first_name ILIKE $2
                       OR u.last_name ILIKE $2
                    ORDER BY u.created_at DESC
                    LIMIT $3 OFFSET $4
                    """,
                    numeric_id, pattern, limit, offset,
                )
                total = await conn.fetchval(
                    """
                    SELECT COUNT(*)::int FROM users u
                    WHERE u.user_id = $1
                       OR u.username ILIKE $2
                       OR u.first_name ILIKE $2
                       OR u.last_name ILIKE $2
                    """,
                    numeric_id, pattern,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT u.*, us.subscription_ends_at,
                           COALESCE((SELECT SUM(ts.count) FROM task_statistics ts
                                     JOIN user_tasks ut ON ut.id = ts.task_id
                                     WHERE ut.user_id = u.id AND ts.date = CURRENT_DATE), 0) AS leads_today,
                           COALESCE((SELECT SUM(ts.count) FROM task_statistics ts
                                     JOIN user_tasks ut ON ut.id = ts.task_id
                                     WHERE ut.user_id = u.id AND ts.date >= date_trunc('month', CURRENT_DATE)), 0) AS leads_month
                    FROM users u
                    LEFT JOIN user_subscriptions us ON us.user_id = u.id
                    WHERE u.username ILIKE $1
                       OR u.first_name ILIKE $1
                       OR u.last_name ILIKE $1
                    ORDER BY u.created_at DESC
                    LIMIT $2 OFFSET $3
                    """,
                    pattern, limit, offset,
                )
                total = await conn.fetchval(
                    """
                    SELECT COUNT(*)::int FROM users u
                    WHERE u.username ILIKE $1
                       OR u.first_name ILIKE $1
                       OR u.last_name ILIKE $1
                    """,
                    pattern,
                )
        else:
            rows = await conn.fetch(
                """
                SELECT u.*, us.subscription_ends_at,
                       COALESCE((SELECT SUM(ts.count) FROM task_statistics ts
                                 JOIN user_tasks ut ON ut.id = ts.task_id
                                 WHERE ut.user_id = u.id AND ts.date = CURRENT_DATE), 0) AS leads_today,
                       COALESCE((SELECT SUM(ts.count) FROM task_statistics ts
                                 JOIN user_tasks ut ON ut.id = ts.task_id
                                 WHERE ut.user_id = u.id AND ts.date >= date_trunc('month', CURRENT_DATE)), 0) AS leads_month
                FROM users u
                LEFT JOIN user_subscriptions us ON us.user_id = u.id
                ORDER BY u.created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit, offset,
            )
            total = await conn.fetchval("SELECT COUNT(*)::int FROM users")

    items = [
        UserListItem(
            id=r["id"],
            user_id=r["user_id"],
            username=r.get("username"),
            first_name=r.get("first_name"),
            last_name=r.get("last_name"),
            created_at=r["created_at"],
            subscription_ends_at=r.get("subscription_ends_at"),
            leads_today=r.get("leads_today", 0),
            leads_month=r.get("leads_month", 0),
        )
        for r in rows
    ]
    return UserListResponse(items=items, total=total or 0)


@app.get("/api/users/{user_id}", dependencies=[Depends(verify_token)])
async def get_user_detail(user_id: uuid.UUID):
    mpool = get_main_pool()
    async with mpool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT u.*, us.subscription_ends_at, us.trial_ends_at
            FROM users u
            LEFT JOIN user_subscriptions us ON us.user_id = u.id
            WHERE u.id = $1
            """,
            user_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        task_rows = await conn.fetch(
            "SELECT id, title, tags, active, created_at FROM user_tasks WHERE user_id = $1 ORDER BY created_at DESC",
            user_id,
        )

    tasks = []
    for t in task_rows:
        tags = t["tags"]
        if isinstance(tags, str):
            tags = json.loads(tags)
        tasks.append(TaskOut(id=t["id"], title=t["title"], tags=tags, active=t["active"], created_at=t["created_at"]))

    return UserDetailResponse(
        id=row["id"],
        user_id=row["user_id"],
        username=row.get("username"),
        first_name=row.get("first_name"),
        last_name=row.get("last_name"),
        balance=row["balance"],
        created_at=row["created_at"],
        subscription_ends_at=row.get("subscription_ends_at"),
        trial_ends_at=row.get("trial_ends_at"),
        tasks=tasks,
    )


@app.get("/api/users/{user_id}/leads", dependencies=[Depends(verify_token)])
async def get_user_leads(
    user_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    date_from: str = Query("", description="Start date YYYY-MM-DD"),
    date_to: str = Query("", description="End date YYYY-MM-DD"),
    task_ids: str = Query("", description="Comma-separated task UUIDs"),
):
    mpool = get_main_pool()
    conditions = ["r.user_id = $1"]
    params: list = [user_id]
    idx = 2

    if date_from.strip():
        conditions.append(f"r.created_at >= ${idx}::timestamptz")
        params.append(date_from.strip() + "T00:00:00Z")
        idx += 1

    if date_to.strip():
        conditions.append(f"r.created_at < ${idx}::timestamptz")
        params.append(date_to.strip() + "T00:00:00Z")
        idx += 1

    if task_ids.strip():
        tids = []
        for tid in task_ids.split(","):
            tid = tid.strip()
            if tid:
                try:
                    tids.append(uuid.UUID(tid))
                except ValueError:
                    pass
        if tids:
            conditions.append(f"r.task_id = ANY(${idx}::uuid[])")
            params.append(tids)
            idx += 1

    where = " AND ".join(conditions)

    async with mpool.acquire() as conn:
        rows = await conn.fetch(
            f"""
            SELECT r.*, ut.title AS task_title
            FROM user_recommendations r
            LEFT JOIN user_tasks ut ON ut.id = r.task_id
            WHERE {where}
            ORDER BY r.created_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
            """,
            *params, limit, offset,
        )
        total = await conn.fetchval(
            f"SELECT COUNT(*)::int FROM user_recommendations r WHERE {where}",
            *params,
        )

    items = []
    for r in rows:
        rec = r["recommendation"]
        if isinstance(rec, str):
            rec = json.loads(rec)
        items.append(
            LeadItem(
                id=r["id"],
                task_id=r["task_id"],
                task_title=r.get("task_title"),
                recommendation=rec if isinstance(rec, dict) else {"text": str(rec)},
                accepted=r["accepted"],
                created_at=r["created_at"],
            )
        )
    return LeadListResponse(items=items, total=total or 0)


@app.get("/api/users/{user_id}/payments", dependencies=[Depends(verify_token)])
async def get_user_payments(
    user_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    mpool = get_main_pool()
    async with mpool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, amount, status, payment, recurrent, created_at, payment_timestamp
            FROM transactions
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            user_id, limit, offset,
        )
        total = await conn.fetchval(
            "SELECT COUNT(*)::int FROM transactions WHERE user_id = $1",
            user_id,
        )

    items = [
        PaymentItem(
            id=r["id"],
            amount=r["amount"],
            status=r["status"],
            payment=r["payment"],
            recurrent=r["recurrent"],
            created_at=r["created_at"],
            payment_timestamp=r.get("payment_timestamp"),
        )
        for r in rows
    ]
    return PaymentListResponse(items=items, total=total or 0)


@app.post("/api/users/{user_id}/balance", dependencies=[Depends(verify_token)])
async def top_up_balance(user_id: uuid.UUID, body: BalanceTopUpRequest):
    mpool = get_main_pool()
    async with mpool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE users SET balance = balance + $2, updated_at = CURRENT_TIMESTAMP WHERE id = $1 RETURNING balance, user_id",
            user_id, body.amount,
        )
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

    # Send Telegram notification
    notification_sent = False
    tg_user_id = row["user_id"]
    token = bot_token()
    if token:
        text = f"\U0001f4b0 На ваш баланс начислено {body.amount} \u20bd\nТекущий баланс: {row['balance']} \u20bd"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": tg_user_id, "text": text},
                )
                tg_body = resp.json()
                notification_sent = resp.status_code == 200 and tg_body.get("ok", False)
                if not notification_sent:
                    logger.warning("Telegram API error for %s: %s", tg_user_id, tg_body)
        except Exception as exc:
            logger.warning("Failed to send balance notification to %s: %s", tg_user_id, exc)

    return BalanceTopUpResponse(new_balance=row["balance"], message=f"Начислено {body.amount} \u20bd", notification_sent=notification_sent)


@app.get("/api/users/{user_id}/tasks", dependencies=[Depends(verify_token)])
async def get_user_tasks(user_id: uuid.UUID):
    mpool = get_main_pool()
    async with mpool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, title FROM user_tasks WHERE user_id = $1 AND active = true ORDER BY created_at DESC",
            user_id,
        )
    return [{"id": str(r["id"]), "title": r["title"]} for r in rows]


# ── UI serving ──────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    if _ui_dir.is_dir():
        return FileResponse(_ui_dir / "index.html")
    return JSONResponse({"service": "admin-ui", "docs": "/docs"})


@app.get("/{path:path}")
async def spa_catch_all(path: str):
    """Serve index.html for all non-API, non-static paths (SPA client-side routing)."""
    if path.startswith("api/") or path.startswith("ui/") or path in ("docs", "redoc", "openapi.json"):
        raise HTTPException(status_code=404, detail="Not found")
    if _ui_dir.is_dir():
        return FileResponse(_ui_dir / "index.html")
    raise HTTPException(status_code=404, detail="Not found")


def main():
    port = int(os.environ.get("PORT", "8011"))
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
