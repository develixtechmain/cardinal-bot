import logging
import os
from pathlib import Path

import asyncpg

from config import database_url_parts

logger = logging.getLogger(__name__)

pool: asyncpg.Pool | None = None


async def init_db() -> None:
    global pool
    if os.environ.get("TRACE_SERVICE_SKIP_DB_INIT") == "1":
        pool = None
        return
    host, port, user, password, database = database_url_parts()
    pool = await asyncpg.create_pool(
        user=user,
        password=password,
        database=database,
        host=host,
        port=port,
        min_size=1,
        max_size=10,
    )
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    sql = schema_path.read_text()
    async with pool.acquire() as conn:
        await conn.execute(sql)
    logger.info("trace_service: schema ensured")


async def close_db() -> None:
    global pool
    if pool:
        await pool.close()
        pool = None


def get_pool() -> asyncpg.Pool:
    if pool is None:
        raise RuntimeError("Database pool not initialized")
    return pool
