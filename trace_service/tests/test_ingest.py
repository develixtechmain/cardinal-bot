import uuid
from unittest.mock import AsyncMock

import pytest

from ingest import ingest_event
from models import TraceEventIngest


@pytest.mark.asyncio
async def test_ingest_event_inserts_and_updates_summary(mock_conn):
    cid = uuid.uuid4()
    body = TraceEventIngest(
        correlation_id=cid,
        service="test",
        stage="one",
        status="ok",
        detail={"chat_id": "-100", "message_id": 1},
        source_chat_id="-100",
        source_message_id=1,
    )
    mock_conn.execute = AsyncMock()
    mock_conn.fetchval = AsyncMock(return_value=99)
    mock_conn.fetch = AsyncMock(
        return_value=[
            {"service": "test", "stage": "one", "status": "ok"},
        ]
    )

    eid = await ingest_event(mock_conn, body)
    assert eid == 99
    assert mock_conn.execute.call_count >= 2
