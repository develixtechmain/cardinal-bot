import logging

import asyncpg

from config import database_url_parts, main_database_url_parts

logger = logging.getLogger(__name__)

pool: asyncpg.Pool | None = None
main_pool: asyncpg.Pool | None = None


async def init_db() -> None:
    global pool, main_pool
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
    logger.info("admin_ui: trace db pool ready")

    mhost, mport, muser, mpassword, mdatabase = main_database_url_parts()
    main_pool = await asyncpg.create_pool(
        user=muser,
        password=mpassword,
        database=mdatabase,
        host=mhost,
        port=mport,
        min_size=1,
        max_size=5,
    )
    logger.info("admin_ui: main db pool ready")


async def close_db() -> None:
    global pool, main_pool
    if pool:
        await pool.close()
        pool = None
    if main_pool:
        await main_pool.close()
        main_pool = None


def get_pool() -> asyncpg.Pool:
    if pool is None:
        raise RuntimeError("Database pool not initialized")
    return pool


def get_main_pool() -> asyncpg.Pool:
    if main_pool is None:
        raise RuntimeError("Main database pool not initialized")
    return main_pool
