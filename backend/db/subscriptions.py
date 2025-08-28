import asyncio
import logging
import uuid

from fastapi import HTTPException

import lava
from db import get_pool

logger = logging.getLogger(__name__)


async def fetch_subscription_by_user_id(user_id: uuid.UUID):
    async with get_pool().acquire() as conn:
        result = await conn.fetchrow("SELECT * FROM user_subscriptions WHERE user_id = $1", user_id)
        if result:
            return result

        result = await conn.fetchrow("INSERT INTO user_subscriptions (user_id) VALUES ($1) RETURNING *", user_id)
        if result:
            return result
        raise Exception("Failed to create subscription")


async def start_subscription_trial(user_id, subscription_id):
    async with get_pool().acquire() as conn:
        subscription = await conn.fetchrow("SELECT * FROM user_subscriptions WHERE user_id = $1 and id = $2", user_id, subscription_id)
        if not subscription:
            raise HTTPException(status_code=400, detail=f"Invalid subscription id {subscription_id} for user {user_id}")

        if subscription['trial_starts_at'] or subscription['trial_ends_at']:
            raise HTTPException(status_code=400, detail=f"Trial already used for subscription {subscription_id}")

        return await conn.fetchrow("UPDATE user_subscriptions SET trial_starts_at = CURRENT_TIMESTAMP, trial_ends_at = CURRENT_TIMESTAMP + INTERVAL '3 days' WHERE id = $1 RETURNING *", subscription_id)


async def init_purchase_for_user(user_id, purchase_request):
    async with get_pool().acquire() as conn:
        subscription = await conn.fetchrow("SELECT * FROM user_subscriptions WHERE user_id = $1", user_id)
        if not subscription:
            raise Exception("Failed to find subscription for init purchase")

        amount = purchase_request.amount
        payment = purchase_request.payment_system
        if payment == 'lava':
            purchase = await lava.init_purchase(purchase_request.email, amount)
        elif payment == 'foo':
            purchase = None
        else:
            raise Exception("Unexpected payment_system for init purchase")

        result = await conn.fetchrow("INSERT INTO transactions (external_id, user_id, subscription_id, amount, payment) VALUES ($1, $2, $3, $4, $5) RETURNING *",
                                     purchase['id'], user_id, subscription['id'], amount, payment)
        if result:
            return result
        raise Exception("Failed to create subscription")


async def check_transactions():
    while True:
        try:
            await _check_transactions()
        except Exception as e:
            logger.error(f"Failed to check pending transactions: {e}")
        await asyncio.sleep(600)


async def _check_transactions():
    processed_ids: set[uuid.UUID] = set()
    while True:
        async with get_pool().acquire() as conn:
            async with conn.transaction():
                trx = await conn.fetchrow(
                    "SELECT id, external_id, status FROM transactions WHERE status = 'pending' AND created_at < CURRENT_TIMESTAMP - INTERVAL '10 minutes' AND NOT (id = ANY($1::uuid[])) FOR UPDATE SKIP LOCKED LIMIT 1",
                    list(processed_ids))
                if not trx:
                    return

                trx_id = trx['id']
                processed_ids.add(trx_id)

                try:
                    new_status = await lava.fetch_transaction_status(trx['external_id'])
                    if trx['status'] != new_status:
                        result = await conn.execute("UPDATE transactions SET status = $2, updated_at = NOW() WHERE id = $1", trx_id, new_status)
                        rows_affected = result.split()[-1]
                        if rows_affected == "1":
                            logger.debug(f"Transaction {trx_id} updated to status: {new_status}")
                        else:
                            logger.warning(f"Transaction {trx_id} already had a new status {new_status}")
                except Exception as e:
                    logger.error(f"Failed to process pending transaction {trx_id}: {e}")
        await asyncio.sleep(1)
