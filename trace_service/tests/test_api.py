import os
import uuid
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("TRACE_SERVICE_SKIP_DB_INIT", "1")
os.environ["TRACE_SERVICE_API_KEY"] = "test-secret-key"

from main import app


@pytest.fixture(autouse=True)
def clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_post_event_unauthorized(patch_db_pool, mock_conn):
    cid = str(uuid.uuid4())
    mock_conn.fetchval = AsyncMock(return_value=1)
    mock_conn.execute = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[{"service": "x", "stage": "y", "status": "ok"}])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/internal/traces/events",
            json={
                "correlation_id": cid,
                "service": "test",
                "stage": "unit",
                "status": "ok",
                "detail": {},
            },
        )
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_post_event_ok(patch_db_pool, mock_conn):
    cid = str(uuid.uuid4())
    mock_conn.fetchval = AsyncMock(return_value=42)
    mock_conn.execute = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[{"service": "test", "stage": "unit", "status": "ok"}])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/internal/traces/events",
            json={
                "correlation_id": cid,
                "service": "test",
                "stage": "unit",
                "status": "ok",
                "detail": {},
            },
            headers={"X-Trace-API-Key": "test-secret-key"},
        )
        assert r.status_code == 200
        j = r.json()
        assert j["correlation_id"] == cid
        assert j["id"] == 42


@pytest.mark.asyncio
async def test_ui_static_served(patch_db_pool):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/ui/styles.css")
        assert r.status_code == 200
        assert b"timeline" in r.content


@pytest.mark.asyncio
async def test_get_trace_not_found(patch_db_pool, mock_conn):
    mock_conn.fetchrow = AsyncMock(return_value=None)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get(
            f"/internal/traces/{uuid.uuid4()}",
            headers={"X-Trace-API-Key": "test-secret-key"},
        )
        assert r.status_code == 404
