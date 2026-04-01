import logging

import asyncpg

from config import database_url_parts

logger = logging.getLogger(__name__)

pool: asyncpg.Pool | None = None


async def init_db() -> None:
    global pool
    host, port, user, password, database = database_url_parts()
    pool = await asyncpg.create_pool(
        user=user,
        password=password,
        database=database,
        host=host,
        port=port,
        min_size=1,
        max_size=5,
    )
    logger.info("admin_ui: db pool ready")


async def close_db() -> None:
    global pool
    if pool:
        await pool.close()
        pool = None


def get_pool() -> asyncpg.Pool:
    if pool is None:
        raise RuntimeError("Database pool not initialized")
    return pool
