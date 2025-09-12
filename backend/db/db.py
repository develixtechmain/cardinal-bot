import logging
import os

import asyncpg
from cachetools import TTLCache

from utils import validate_env

pool: asyncpg.pool.Pool

users_cache = TTLCache(maxsize=100, ttl=300)
onboarding_cache = TTLCache(maxsize=100, ttl=1200)
rules_cache = TTLCache(maxsize=100, ttl=3600)

logger = logging.getLogger(__name__)


async def init_postgresql():
    global pool

    validate_env("DB_PASS")

    password = os.environ["DB_PASS"]

    pool = await asyncpg.create_pool(
        user=os.environ.get("DB_USER", "cardinal"),
        password=password,
        database=os.environ.get("DB_NAME", "cardinal"),
        host=os.environ.get("DB_HOST", "postgresql"),
        port=os.environ.get("DB_PORT", 5432),
        min_size=10,
        max_size=20
    )

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("""
                            CREATE TABLE IF NOT EXISTS versions (
                                id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
                                rev BIGINT NOT NULL UNIQUE,
                                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
                            )
                        """)

            result = await conn.fetchrow("SELECT * FROM versions ORDER BY created_at DESC LIMIT 1")
            if result:
                rev = result['rev']
            else:
                rev = 0

            if rev < 1:
                rev = await bump(conn, _0_0_1)

            logger.info(f"Current DB revision: {rev}")


async def bump(conn, rev):
    revision = await rev(conn)
    result = await conn.fetchrow("INSERT INTO versions (rev) VALUES ($1) RETURNING id", revision)
    if result:
        logger.info(f"DB revision bumped to {revision} version")
        return revision
    raise Exception(f"Failed to bump DB revision to {revision}")


async def _0_0_1(conn):
    await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
                    user_id BIGINT NOT NULL UNIQUE,
                    first_name VARCHAR(255) NOT NULL,
                    last_name VARCHAR(255) NOT NULL,
                    username VARCHAR(255) NOT NULL,
                    avatar_url TEXT,
                    referrer_id UUID,
                    balance BIGINT NOT NULL DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """)
    await conn.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'onboarding_status') THEN
                        CREATE TYPE onboarding_status AS ENUM ('uncompleted', 'completed');
                    END IF;
                    
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_status') THEN
                        CREATE TYPE transaction_status AS ENUM ('pending', 'completed', 'failed', 'timeout');
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_payment') THEN
                        CREATE TYPE transaction_payment AS ENUM ('lava', 'alpha', 'balance');
                    END IF;
                END $$;
            """)
    await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_onboardings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
                    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                    questions JSONB NOT NULL DEFAULT '[]'::jsonb,
                    status onboarding_status NOT NULL DEFAULT 'uncompleted',
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """)
    await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_tasks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    tags JSONB NOT NULL,
                    active BOOLEAN NOT NULL DEFAULT true,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """)
    await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_channels (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    chat_id BIGINT NOT NULL,
                    active BOOLEAN NOT NULL DEFAULT true,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    UNIQUE (user_id, chat_id)
                )
            """)
    await conn.execute("""
                CREATE TABLE IF NOT EXISTS recommendations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    task_id UUID NOT NULL REFERENCES user_tasks(id),
                    recommendation JSONB NOT NULL,
                    accepted BOOLEAN,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """)
    await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_subscriptions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
                    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                    trial_starts_at TIMESTAMPTZ,
                    trial_ends_at TIMESTAMPTZ,
                    subscription_ends_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """)
    await conn.execute("""
                CREATE TABLE IF NOT EXISTS task_statistics (
                    task_id UUID NOT NULL REFERENCES user_tasks(id),
                    date DATE NOT NULL DEFAULT CURRENT_DATE,
                    count INT NOT NULL DEFAULT 0,
                    PRIMARY KEY (task_id, date)
                )
            """)
    await conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
                    external_id UUID NOT NULL,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    subscription_id UUID NOT NULL REFERENCES user_subscriptions(id),
                    amount BIGINT NOT NULL,
                    status transaction_status NOT NULL,
                    payment transaction_payment NOT NULL,
                    payment_timestamp TIMESTAMPTZ,
                    recurrent BOOL DEFAULT TRUE NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """)
    await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_task_rules (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
                    task_id UUID NOT NULL REFERENCES user_tasks(id) ON DELETE CASCADE,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    rules TEXT[] NOT NULL
                )
            """)
    await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id ON users(id);
                CREATE INDEX IF NOT EXISTS idx_user_tg_id ON users(user_id);
                CREATE INDEX IF NOT EXISTS idx_user_referrer_id ON users(referrer_id);
                CREATE INDEX IF NOT EXISTS idx_channels_user_id ON user_channels(user_id);
                CREATE INDEX IF NOT EXISTS idx_onboardings_user_id ON user_onboardings(user_id);
                CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON user_subscriptions(user_id);
                CREATE INDEX IF NOT EXISTS idx_user_tasks_user_id ON user_tasks(user_id);
                CREATE INDEX IF NOT EXISTS idx_task_statistics_task_id ON task_statistics(task_id);
                CREATE INDEX IF NOT EXISTS idx_task_statistics_date ON task_statistics(date);
                CREATE INDEX IF NOT EXISTS idx_task_statistics_task_id_date ON task_statistics(task_id, date);
                CREATE INDEX IF NOT EXISTS idx_transactions_external_id ON transactions(external_id);
                CREATE INDEX IF NOT EXISTS idx_transactions_pending_latest ON transactions (external_id, amount, created_at DESC) WHERE status = 'pending';
                CREATE INDEX IF NOT EXISTS idx_transactions_pending_created_at ON transactions (created_at) WHERE status = 'pending';
                CREATE INDEX IF NOT EXISTS idx_transactions_pending_created_at ON transactions (created_at) WHERE status = 'pending';
                CREATE UNIQUE INDEX IF NOT EXISTS ux_transactions_external_id_payment_timestamp ON transactions(external_id, payment_timestamp) WHERE payment_timestamp IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_user_task_rules_user_id_task_id ON user_task_rules(user_id, task_id);
            """)

    return 1


async def disconnect():
    await pool.close()
    logger.info("PostgreSQL pool closed.")


def get_pool():
    return pool
