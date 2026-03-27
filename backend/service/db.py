import logging
import os
import random
from datetime import datetime, timedelta
from typing import Optional

import asyncpg
from cachetools import TTLCache

from utils import validate_env

pool: asyncpg.Pool

users_cache = TTLCache(maxsize=100, ttl=300)
rules_cache = TTLCache(maxsize=100, ttl=3600)
_task_stats_cache = TTLCache(maxsize=1000, ttl=86400)
_notification_limits_cache = TTLCache(maxsize=1000, ttl=86400)

logger = logging.getLogger(__name__)

_task_stats_cache_empty_till: Optional[datetime] = None


def task_stats_cache_clear():
    global _task_stats_cache_empty_till
    _task_stats_cache.clear()
    _task_stats_cache_empty_till = datetime.now() + timedelta(minutes=20)
    logger.info("Task stats cache cleared")


def get_task_stats(task_id):
    if _task_stats_cache_empty_till is not None:
        now = datetime.now()
        if now < _task_stats_cache_empty_till:
            logger.info(f"Task {task_id} stat cache ignored")
            return None
    logger.info(f"Task {task_id} stat cache hit")
    return _task_stats_cache.get(task_id)


def set_task_stats(task_id):
    if _task_stats_cache_empty_till is not None:
        now = datetime.now()
        if now < _task_stats_cache_empty_till:
            _task_stats_cache[task_id] = True
            logger.info(f"Task {task_id} stat cache inserted")
    else:
        _task_stats_cache[task_id] = True
        logger.info(f"Task {task_id} stat cache inserted")


def notification_limits_cache_clear():
    _notification_limits_cache.clear()


def get_user_notification_limits(user_id, min_value=20, max_value=33):
    user_limits = _notification_limits_cache.get(user_id)
    if user_limits is None:
        user_limits = random.randint(min_value, max_value)
        _notification_limits_cache[user_id] = user_limits
    return user_limits


async def init_postgresql():
    global pool

    validate_env("DB_PASS")

    password = os.environ["DB_PASS"]

    # noinspection PyUnresolvedReferences
    pool = await asyncpg.create_pool(
        user=os.environ.get("DB_USER", "cardinal"),
        password=password,
        database=os.environ.get("DB_NAME", "cardinal"),
        host=os.environ.get("DB_HOST", "postgresql"),
        port=int(os.environ.get("DB_PORT", 5432)),
        min_size=10,
        max_size=20,
    )

    async with pool.acquire() as conn:
        async with conn.transaction():
            # fmt: off
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS versions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
                    rev BIGINT NOT NULL UNIQUE,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
                );
            """)

            # fmt: on
            result = await conn.fetchrow("SELECT * FROM versions ORDER BY created_at DESC, rev DESC LIMIT 1;")
            if result:
                rev = result["rev"]
            else:
                rev = 0

        for i, migration in enumerate([_0_0_1, _0_0_2, _0_0_3, _0_0_4], start=1):
            if rev < i:
                rev = await bump(conn, migration)

        logger.info(f"Current DB revision: {rev}")


async def bump(conn, rev):
    async with conn.transaction():
        revision = await rev(conn)
        result = await conn.fetchrow("INSERT INTO versions (rev) VALUES ($1) RETURNING id;", revision)
        if result:
            logger.info(f"DB revision bumped to {revision} version")
            return revision
        raise Exception(f"Failed to bump DB revision to {revision}")


# fmt: off
async def _0_0_1(conn):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
            user_id BIGINT NOT NULL UNIQUE,
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            username VARCHAR(255),
            avatar_url TEXT,
            referrer_id UUID,
            balance BIGINT NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
    """)
    await conn.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'onboarding_status') THEN
                CREATE TYPE onboarding_status AS ENUM ('uncompleted', 'completed');
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_status') THEN
                CREATE TYPE transaction_status AS ENUM ('template', 'pending', 'completed', 'failed', 'timeout');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_payment') THEN
                CREATE TYPE transaction_payment AS ENUM ('lava', 'alpha', 'balance');
            END IF;
        END $$;
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_onboardings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            questions JSONB NOT NULL DEFAULT '[]'::jsonb,
            status onboarding_status NOT NULL DEFAULT 'uncompleted',
            answers SMALLINT NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_tasks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            tags JSONB NOT NULL,
            active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_channels (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            chat_id BIGINT NOT NULL,
            active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
            UNIQUE (user_id, chat_id)
        );
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_recommendations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            task_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000000'::uuid REFERENCES user_tasks(id) ON DELETE SET DEFAULT,
            recommendation JSONB NOT NULL,
            accepted BOOLEAN,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_subscriptions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
            user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            trial_starts_at TIMESTAMPTZ,
            trial_ends_at TIMESTAMPTZ,
            subscription_ends_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS task_statistics (
            task_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000000'::uuid REFERENCES user_tasks(id) ON DELETE SET DEFAULT,
            date DATE NOT NULL DEFAULT CURRENT_DATE,
            count INT NOT NULL DEFAULT 0
        );
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
        );
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_task_rules (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
            task_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000000'::uuid REFERENCES user_tasks(id) ON DELETE SET DEFAULT,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            rules TEXT[] NOT NULL
        );
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS telegram_messages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
            message JSONB NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
    """)
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_id ON users(id);
        CREATE INDEX IF NOT EXISTS idx_user_tg_id ON users(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_referrer_id ON users(referrer_id);
        CREATE INDEX IF NOT EXISTS idx_user_channels_user_id ON user_channels(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_onboardings_user_id ON user_onboardings(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_tasks_user_id ON user_tasks(user_id);
        CREATE INDEX IF NOT EXISTS idx_task_statistics_task_id ON task_statistics(task_id);
        CREATE INDEX IF NOT EXISTS idx_task_statistics_date ON task_statistics(date);
        CREATE INDEX IF NOT EXISTS idx_transactions_external_id ON transactions(external_id);
        CREATE INDEX IF NOT EXISTS idx_transactions_pending_latest ON transactions (external_id, amount, created_at DESC) WHERE status = 'pending';
        CREATE INDEX IF NOT EXISTS idx_transactions_pending_created_at ON transactions (created_at) WHERE status = 'pending';
        CREATE UNIQUE INDEX IF NOT EXISTS ux_task_statistics_task_id_date ON task_statistics (task_id, date) WHERE task_id != '00000000-0000-0000-0000-000000000000';
        CREATE UNIQUE INDEX IF NOT EXISTS ux_transactions_external_id_payment_timestamp ON transactions(external_id, payment_timestamp) WHERE payment_timestamp IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_user_task_rules_user_id_task_id ON user_task_rules(user_id, task_id);
    """)

    await conn.execute("INSERT INTO users (id, user_id, first_name, last_name, username) VALUES ('00000000-0000-0000-0000-000000000000', 0, 'Deleted', 'Deleted', 'Deleted') ON CONFLICT (id) DO NOTHING;")
    await conn.execute("INSERT INTO user_tasks (id, user_id, title, tags, active) VALUES ('00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Deleted', 'null', FALSE) ON CONFLICT (id) DO NOTHING;")

    return 1

async def _0_0_2(conn):
    await conn.execute("ALTER TYPE transaction_payment ADD VALUE 'robokassa';")
    await conn.execute("CREATE SEQUENCE IF NOT EXISTS transactions_sequence START 1;")

    await conn.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS number BIGINT DEFAULT nextval('transactions_sequence');")
    await conn.execute("""
        WITH ordered AS (SELECT id, row_number() OVER (ORDER BY created_at) AS row FROM transactions)
        UPDATE transactions t SET number = o.row FROM ordered o WHERE t.id = o.id;
    """)

    await conn.execute("SELECT setval('transactions_sequence', (SELECT MAX(number) FROM transactions));")
    await conn.execute("ALTER TABLE transactions ALTER COLUMN number SET NOT NULL;")

    await conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_transactions_number ON transactions(number);")

    return 2


async def _0_0_3(conn):
    await conn.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'channel_type') THEN
                    CREATE TYPE channel_type AS ENUM ('core', 'recommendation');
                END IF;
            END $$;
        """)

    await conn.execute("ALTER TABLE user_channels ADD COLUMN IF NOT EXISTS channel_type channel_type;")
    await conn.execute("UPDATE user_channels SET channel_type = 'recommendation' WHERE channel_type IS NULL;")
    await conn.execute("ALTER TABLE user_channels ALTER COLUMN channel_type SET NOT NULL;")

    await conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_user_channels_user_id_chat_id_channel_type ON user_channels(user_id, chat_id, channel_type);")
    await conn.execute("DROP INDEX IF EXISTS idx_user_channels_user_id;")
    await conn.execute("ALTER TABLE user_channels DROP CONSTRAINT IF EXISTS user_channels_user_id_chat_id_key;")

    return 3


async def _0_0_4(conn):
    await conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_notifications (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
                        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        task_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000000'::uuid REFERENCES user_tasks(id) ON DELETE SET DEFAULT,
                        notification_type VARCHAR(255) NOT NULL,
                        payload JSONB NOT NULL DEFAULT '{}'::jsonb,
                        date DATE NOT NULL DEFAULT CURRENT_DATE
                    );
                """)

    await conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_user_notification ON user_notifications(user_id, task_id, notification_type);")

    return 4


# fmt: on
async def disconnect():
    global pool
    await pool.close()
    logger.info("PostgreSQL pool closed.")


def get_pool():
    return pool
