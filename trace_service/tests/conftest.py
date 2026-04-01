from unittest.mock import AsyncMock, MagicMock

import pytest


class _ConnCtx:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *args):
        return None


@pytest.fixture
def mock_conn():
    m = AsyncMock()
    tx = MagicMock()
    tx.__aenter__ = AsyncMock(return_value=m)
    tx.__aexit__ = AsyncMock(return_value=None)
    m.transaction = MagicMock(return_value=tx)
    return m


@pytest.fixture
def mock_pool(mock_conn):
    pool = MagicMock()
    pool.acquire = MagicMock(return_value=_ConnCtx(mock_conn))
    return pool


@pytest.fixture
def patch_db_pool(monkeypatch, mock_pool):
    import db as db_mod

    async def fake_init():
        db_mod.pool = mock_pool

    async def fake_close():
        db_mod.pool = None

    monkeypatch.setattr(db_mod, "init_db", fake_init)
    monkeypatch.setattr(db_mod, "close_db", fake_close)
    db_mod.pool = mock_pool
    yield mock_pool
    db_mod.pool = None
