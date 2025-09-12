import asyncio
import logging
import uuid
from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import Optional

import asyncpg
from asyncpg import Record
from fastapi import HTTPException
from pydantic import BaseModel

import lava
from db import get_pool, users_cache

logger = logging.getLogger(__name__)


class IgnoreWebhookException(Exception):
    pass


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TransactionPayment(str, Enum):
    LAVA = "lava"
    ALPHA = "alpha"
    BALANCE = 'balance'


class WebhookStatus(str, Enum):
    COMPLETED = "completed"
    COMPLETED_NEW = "completed_new"
    FAILED = "failed"
    FAILED_NEW = "failed_new"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

    @classmethod
    def from_lava(cls, event: str, error: str) -> Optional["WebhookStatus"]:
        if event == "payment.success":
            return cls.COMPLETED
        if event == "subscription.recurring.payment.success":
            return cls.COMPLETED_NEW
        if event == "payment.failed":
            if error == "Payment window is opened but not completed":
                return cls.TIMEOUT
            return cls.FAILED
        if event == "subscription.recurring.payment.failed":
            return cls.FAILED_NEW
        if event == "subscription.cancelled":
            return cls.CANCELLED
        return None


class SubscriptionWebhook(BaseModel):
    id: uuid.UUID
    amount: int
    currency: str
    status: WebhookStatus
    payment: TransactionPayment
    paymentTimestamp: datetime


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
        subscription = await conn.fetchrow("SELECT * FROM user_subscriptions WHERE user_id = $1 AND id = $2", user_id, subscription_id)
        if not subscription:
            raise HTTPException(status_code=400, detail=f"Invalid subscription id {subscription_id} for user {user_id}")

        if subscription['trial_starts_at'] or subscription['trial_ends_at']:
            raise HTTPException(status_code=400, detail=f"Trial already used for subscription {subscription_id}")

        return await conn.fetchrow("UPDATE user_subscriptions SET trial_starts_at = CURRENT_TIMESTAMP, trial_ends_at = CURRENT_TIMESTAMP + INTERVAL '3 days' WHERE id = $1 RETURNING *", subscription_id)


async def init_purchase_for_user(user_id, purchase_request):
    async with get_pool().acquire() as conn:
        subscription = await conn.fetchrow("SELECT * FROM user_subscriptions WHERE user_id = $1", user_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Failed to find subscription for init purchase")

        months = purchase_request.months
        payment = purchase_request.payment_system
        if payment == TransactionPayment.LAVA:
            purchase = await lava.init_purchase(purchase_request.email, months)
        elif payment == TransactionPayment.ALPHA:
            purchase = None
        else:
            raise HTTPException(status_code=400, detail="Unexpected payment_system for init purchase")

        result = await conn.fetchrow("INSERT INTO transactions (external_id, user_id, subscription_id, amount, payment) VALUES ($1, $2, $3, $4, $5) RETURNING *",
                                     purchase['id'], user_id, subscription['id'], purchase['price'], TransactionPayment.BALANCE)
        if result:
            return purchase
        raise Exception("Failed to create subscription")


async def purchase_from_user_balance(user_id):
    async with get_pool().acquire() as conn:
        subscription = await conn.fetchrow("SELECT * FROM user_subscriptions WHERE user_id = $1", user_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Failed to find subscription for purchase")

        async with conn.transaction():
            result = await conn.fetchrow("INSERT INTO transactions (external_id, user_id, subscription_id, amount, status, payment) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *",
                                         uuid.UUID(int=0), user_id, subscription['id'], 4900, TransactionStatus.COMPLETED, TransactionPayment.BALANCE)
            if result:
                await _update_user_balance(conn, user_id, -4900)
                result = await conn.fetchrow(
                    """
                    UPDATE user_subscriptions SET subscription_ends_at = CASE
                        WHEN subscription_ends_at > CURRENT_TIMESTAMP
                             THEN subscription_ends_at + INTERVAL '1 month'
                        ELSE CURRENT_TIMESTAMP + INTERVAL '1 month'
                    END WHERE id = $1 RETURNING *
                    """,
                    subscription['id']
                )
        if result:
            users_cache.pop(user_id, None)
            return result

        raise Exception("Failed to create subscription")


async def disable_recurrency_for_user(user_id):
    async with get_pool().acquire() as conn:
        # subscriptions could be more suitable but multiple external_id or payment is possible issue-moment
        active_transactions = await conn.execute("SELECT DISTINCT ON (external_id) * FROM transactions WHERE user_id = $1 AND recurrent IS TRUE ORDER BY created_at DESC", user_id)
        payments = defaultdict(list)
        for trx in active_transactions:
            payments[trx['payment']].append(trx)
        tasks = [lava.disable_recurrency_for_user(payments[TransactionPayment.LAVA])]
        results = await asyncio.gather(*tasks)

        final_result = defaultdict(list)
        for result in results:
            for key in ('success', 'failed'):
                final_result[key].extend(result[key])

        result = await conn.fetchrow("UPDATE transactions SET recurrent = FALSE, updated_at = CURRENT_TIMESTAMP WHERE external_id IN $1", [trx['external_id'] for trx in final_result['success']])
        if result:
            logger.debug(f"Disable recurring for user finished with {len(final_result['success'])} success and {len(final_result['failed'])} failed transactions, marked")
        else:
            logger.debug(f"Disable recurring for user finished with {len(final_result['success'])} success and {len(final_result['failed'])} failed transactions, not marked")


async def check_transactions():
    while True:
        try:
            await _check_transactions()
        except Exception as e:
            logger.error(f"Failed to check pending transactions: {e}")
        await asyncio.sleep(600)


async def _check_transactions():
    while True:
        trx_id = None
        async with get_pool().acquire() as conn:
            try:
                async with conn.transaction():
                    trx = await conn.fetchrow(
                        "SELECT id, external_id, status FROM transactions WHERE status = 'pending' AND created_at < CURRENT_TIMESTAMP - INTERVAL '10 minutes' FOR UPDATE SKIP LOCKED LIMIT 1")
                    if not trx:
                        return

                trx_id = trx['id']

                new_status = await lava.fetch_transaction_status(trx['external_id'])
                if trx['status'] != new_status:
                    async with conn.transaction():
                        result = await conn.fetchrow("UPDATE transactions SET status = $3, updated_at = CURRENT_TIMESTAMP WHERE id = $1 AND status = $2 RETURNING id", trx_id, trx['status'], new_status)
                        if result:
                            logger.debug(f"Transaction {trx_id} updated to status: {new_status}")
                        else:
                            logger.warning(f"Transaction {trx_id} already had a new status {new_status}")
            except Exception as e:
                if trx_id:
                    logger.error(f"Failed to process pending transaction {trx_id}: {e}")
                else:
                    logger.error(f"Failed to select pending transaction: {e}")
        await asyncio.sleep(1)


async def handle_webhook(webhook: SubscriptionWebhook) -> None:
    try:
        if webhook.currency != "RUB":
            raise IgnoreWebhookException(f"Unsupported currency: {webhook.currency}")
        async with get_pool().acquire() as conn:
            async with conn.transaction():
                if webhook.status == WebhookStatus.FAILED_NEW:
                    await _insert_recurring_transaction(conn, webhook, TransactionStatus.FAILED)
                elif webhook.status in (WebhookStatus.FAILED, WebhookStatus.TIMEOUT):
                    await _update_transaction_status(conn, webhook)
                elif webhook.status == WebhookStatus.CANCELLED:
                    info = await conn.fetchrow("""
                            SELECT s.id AS subscription_id, s.user_id, t.id AS trx_id
                            FROM transactions t INNER JOIN user_subscriptions s ON s.id = t.subscription_id
                            WHERE t.external_id = $1 LIMIT 1
                        """, webhook.id)
                    if info:
                        logger.error(f"SUBSCRIPTION CANCELLED id:{info['subscription_id']} trx_id:{info['trx_id']}|{webhook.id} user_id: {info['user_id']}")
                    else:
                        raise IgnoreWebhookException(f"No transactions found for cancelled subscription {webhook.id} ")
                elif webhook.status == WebhookStatus.COMPLETED:
                    trx = await _update_transaction_status(conn, webhook)
                    await _update_user_balance(conn, trx['user_id'], webhook.amount)
                elif webhook.status == WebhookStatus.COMPLETED_NEW:
                    trx = await _insert_recurring_transaction(conn, webhook, TransactionStatus.COMPLETED)
                    await _update_user_balance(conn, trx['user_id'], webhook.amount)
                else:
                    raise Exception(f"Unexpected webhook status {webhook.status}")
    except IgnoreWebhookException as e:
        logger.warning(f"Suppressed {webhook.payment} webhook: {e}")
    except Exception as e:
        logger.warning(f"Failed to process {webhook.payment} webhook: {e}")
        raise Exception(f"Failed to process {webhook.payment} webhook") from e


async def _insert_recurring_transaction(conn: asyncpg.Connection, webhook: SubscriptionWebhook, status: TransactionStatus) -> Record:
    try:
        trx = await conn.fetchrow("""
                INSERT INTO transactions (external_id, user_id, subscription_id, amount, payment, status, payment_timestamp)
                SELECT $1, t.user_id, t.subscription_id, $2, $3, $4, $5
                FROM transactions t
                WHERE t.external_id = $1 LIMIT 1 RETURNING id, user_id
            """, webhook.id, webhook.amount, webhook.payment, status, webhook.paymentTimestamp)

        if trx:
            logger.debug(f"Recurring transaction {trx['id']}|{webhook.id} inserted with {status} status")
            return trx
        else:
            raise IgnoreWebhookException(f"No transactions {webhook.id} found or insert failed")
    except asyncpg.exceptions.UniqueViolationError:
        logger.info(f"Ignoring duplicate {webhook.payment} webhook {webhook.id} {webhook.paymentTimestamp}")
        raise IgnoreWebhookException("Webhook already processed")


async def _update_transaction_status(conn: asyncpg.Connection, webhook: SubscriptionWebhook) -> Record:
    try:
        trx = await conn.fetchrow("""
            UPDATE transactions t
            SET status = $3, updated_at = CURRENT_TIMESTAMP, payment_timestamp = COALESCE(payment_timestamp, $4)
            FROM (
                SELECT id FROM transactions
                WHERE external_id = $1 AND amount = $2 AND status = 'pending'
                ORDER BY created_at DESC FOR UPDATE SKIP LOCKED LIMIT 1
            ) it WHERE t.id = it.id RETURNING t.id, t.user_id
        """, webhook.id, webhook.amount, webhook.status, webhook.paymentTimestamp)

        if trx:
            logger.debug(f"Transaction {trx['id']}|{webhook.id} updated to status: {webhook.status}")
            return trx
        else:
            raise IgnoreWebhookException(f"No pending transactions {webhook.id} for {webhook.amount}")
    except asyncpg.exceptions.UniqueViolationError:
        logger.info(f"Ignoring duplicate {webhook.payment} webhook {webhook.id} {webhook.timestamp}")
        raise IgnoreWebhookException("Webhook already processed")


async def _update_user_balance(conn: asyncpg.Connection, user_id: uuid.UUID, amount: int) -> None:
    row = await conn.fetchrow("UPDATE users SET balance = balance + $2 WHERE id = $1 RETURNING balance - $2 AS old_balance, balance AS new_balance", user_id, amount)
    if row:
        logger.debug(f"User {user_id} balance updated from {row['old_balance']} to {row['new_balance']}")
    else:
        raise Exception(f"Failed to update user {user_id} balance for {amount}")
