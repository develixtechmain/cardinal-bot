import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

import asyncpg
from asyncpg import Record
from fastapi import HTTPException, Request
from pydantic import BaseModel

from bot.notification.notification import NotificationType
from bot.notification.queue import push_notification_with_payload
from consts import TransactionPayment, TransactionStatus, get_months_by_price, get_price_by_months
from external.payment import alpha, lava, robo
from service import payments_completed_total, revenue_total, users_trials_total
from service.db import get_pool, get_user_notification_limits, users_cache

logger = logging.getLogger(__name__)


class IgnoreWebhookException(Exception):
    pass


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
    payment_timestamp: datetime


async def fetch_subscription_by_user_id(user_id: uuid.UUID | int, from_tg: bool = False):
    if from_tg:
        async with get_pool().acquire() as conn:
            result = await conn.fetchrow("SELECT us.* FROM user_subscriptions us INNER JOIN users u ON u.id = us.user_id WHERE u.user_id = $1;", user_id)
            if result:
                return result

            result = await conn.fetchrow("INSERT INTO user_subscriptions (user_id) SELECT id FROM users WHERE user_id = $1 RETURNING *;", user_id)
            if result:
                return result
            raise Exception("Failed to create subscription")
    else:
        async with get_pool().acquire() as conn:
            result = await conn.fetchrow("SELECT * FROM user_subscriptions WHERE user_id = $1;", user_id)
            if result:
                return result

            result = await conn.fetchrow("INSERT INTO user_subscriptions (user_id) VALUES ($1) RETURNING *;", user_id)
            if result:
                return result
            raise Exception("Failed to create subscription")


async def start_subscription_trial(user_id, subscription_id):
    async with get_pool().acquire() as conn:
        subscription = await conn.fetchrow("SELECT * FROM user_subscriptions WHERE user_id = $1;", user_id)
        if not subscription:
            raise HTTPException(status_code=400, detail=f"Invalid subscription id {subscription_id} for user {user_id}")

        if subscription["trial_starts_at"] or subscription["trial_ends_at"] or subscription["subscription_ends_at"]:
            raise HTTPException(status_code=400, detail=f"Trial is not available for subscription {subscription_id}")

        result = await conn.fetchrow("UPDATE user_subscriptions SET trial_starts_at = CURRENT_TIMESTAMP, trial_ends_at = CURRENT_TIMESTAMP + INTERVAL '3 days' WHERE id = $1 RETURNING *;", subscription_id)
        if result:
            users_trials_total.labels(user_id=str(user_id)).inc()
            return result
        raise Exception(f"Failed to start trial for subscription {subscription_id}")


async def init_purchase_for_user(user_id, purchase_request):
    months = purchase_request.months
    payment = purchase_request.payment_system
    price = get_price_by_months(months)

    async with get_pool().acquire() as conn:
        subscription = await conn.fetchrow("SELECT * FROM user_subscriptions WHERE user_id = $1;", user_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Failed to find subscription for init purchase")

        try:
            insert_transaction_query = "INSERT INTO transactions (external_id, user_id, subscription_id, amount, payment, status) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *;"
            if payment == TransactionPayment.LAVA:
                purchase = await lava.init_purchase(purchase_request.email, price)
                trx = await conn.fetchrow(insert_transaction_query, purchase["id"], user_id, subscription["id"], price, TransactionPayment.LAVA, TransactionStatus.PENDING)
            elif payment == TransactionPayment.ROBOKASSA:
                trx = await conn.fetchrow(insert_transaction_query, uuid.UUID(int=0), user_id, subscription["id"], price, TransactionPayment.ROBOKASSA, TransactionStatus.PENDING)
                purchase = await robo.init_purchase(months, purchase_request.email, price, trx["number"])
            elif payment == TransactionPayment.ALPHA:
                trx = await conn.fetchrow(insert_transaction_query, uuid.UUID(int=0), user_id, subscription["id"], price, TransactionPayment.ALPHA, TransactionStatus.TEMPLATE)
                purchase = await alpha.init_purchase(trx["id"], months, purchase_request.email, price)
                update_transaction_status_query = "UPDATE transactions SET external_id = $2, status = 'pending', updated_at = CURRENT_TIMESTAMP WHERE id = $1 AND status = 'template' RETURNING *;"
                trx = await conn.fetchrow(update_transaction_status_query, trx["id"], purchase["id"])
                if not trx:
                    raise Exception("Failed to set alpha transaction to pending status")
            else:
                raise HTTPException(status_code=400, detail="Unexpected payment_system for init purchase")
        except Exception:
            logger.warning("Failed init purchase", exc_info=True)
            raise

        if trx:
            purchase["id"] = trx["id"]
            return purchase
        raise Exception("Failed to create subscription")


async def complete_robokassa_purchase_for_user(request: Request):
    async with get_pool().acquire() as conn:
        success, params = await robo.complete_purchase(request)
        number = int(params["inv_id"])
        amount = int(params["out_sum"].split(".")[0])

        trx = await conn.fetchrow("SELECT * FROM transactions WHERE number = $1", number)
        if not trx or trx["payment"] != TransactionPayment.ROBOKASSA:
            raise HTTPException(status_code=404, detail=f"Order {number} not found")
        if trx["amount"] != amount:
            logger.error(f"Transaction {number} paid with wrong amount!")
            raise HTTPException(status_code=400, detail=f"Unexpected paid amount for {number}")

        trx_id = trx["id"]
        status = trx["status"]
        if status == TransactionStatus.COMPLETED:
            result = await conn.fetchrow("SELECT * FROM user_subscriptions WHERE id = $1", trx["subscription_id"])
            if result:
                return result
            else:
                raise HTTPException(status_code=404, detail=f"Failed to fetch subscription {trx['subscription_id']}")
        elif status != TransactionStatus.PENDING:
            raise HTTPException(status_code=409, detail=f"Transaction {trx_id} is not pending")

        new_status = TransactionStatus.COMPLETED if success else TransactionStatus.FAILED
        if status == new_status:
            raise HTTPException(status_code=409, detail=f"Transaction {trx_id} is not updated")
        else:
            async with conn.transaction():
                trx = await conn.fetchrow("UPDATE transactions SET status = $3, updated_at = CURRENT_TIMESTAMP WHERE id = $1 AND status = $2 RETURNING *;", trx_id, status, new_status)
                if trx:
                    logger.debug(f"Transaction {trx_id} updated to status: {new_status}")
                else:
                    raise HTTPException(status_code=409, detail=f"Transaction {trx_id} already has a new status")

                if new_status == TransactionStatus.COMPLETED:
                    result = await _prolong_subscription(conn, trx["subscription_id"], amount)
                elif new_status != TransactionStatus.FAILED:
                    result = await conn.fetchrow("SELECT * FROM user_subscriptions WHERE id = $1;", trx["subscription_id"])
                else:
                    result = None
                    asyncio.create_task(_inform_user_purchase_failed(trx["user_id"]))

                if result:
                    revenue_total.inc(trx["amount"])
                    payments_completed_total.labels(user_id=str(trx["user_id"])).inc()
                    asyncio.create_task(_inform_user_prolong(trx["user_id"]))
                    return result
        raise Exception("Failed to complete robokassa purchase")


async def complete_alpha_purchase_for_user(external_id):
    async with get_pool().acquire() as conn:
        trx = await conn.fetchrow("SELECT * FROM transactions WHERE external_id = $1;", external_id)
        if not trx or trx["payment"] != TransactionPayment.ALPHA:
            raise HTTPException(status_code=404, detail=f"Order {external_id} not found")

        trx_id = trx["id"]
        status = trx["status"]
        if status == TransactionStatus.COMPLETED:
            result = await conn.fetchrow("SELECT * FROM user_subscriptions WHERE id = $1;", trx["subscription_id"])
            if result:
                return result
            else:
                raise Exception(f"Failed to fetch subscription {trx['subscription_id']}")
        elif status != TransactionStatus.PENDING:
            raise HTTPException(status_code=409, detail=f"Transaction {trx_id} is not pending")

        new_status = await alpha.fetch_order_status(external_id)
        if status == new_status:
            raise HTTPException(status_code=409, detail=f"Transaction {trx_id} is not updated")
        else:
            async with conn.transaction():
                trx = await conn.fetchrow("UPDATE transactions SET status = $3, updated_at = CURRENT_TIMESTAMP WHERE id = $1 AND status = $2 RETURNING *;", trx_id, status, new_status)
                if trx:
                    logger.debug(f"Transaction {trx_id} updated to status: {new_status}")
                else:
                    raise Exception(f"Transaction {trx_id} already has a new status")

                if new_status == TransactionStatus.COMPLETED:
                    result = await _prolong_subscription(conn, trx["subscription_id"], trx["amount"])
                elif new_status != TransactionStatus.FAILED:
                    result = await conn.fetchrow("SELECT * FROM user_subscriptions WHERE id = $1;", trx["subscription_id"])
                else:
                    result = None
                    asyncio.create_task(_inform_user_purchase_failed(trx["user_id"]))

                if result:
                    revenue_total.inc(trx["amount"])
                    payments_completed_total.labels(user_id=str(trx["user_id"])).inc()
                    asyncio.create_task(_inform_user_prolong(trx["user_id"]))
                    return result

        raise Exception("Failed to complete purchase")


async def check_purchase_for_user(user_id, trx_id):
    async with get_pool().acquire() as conn:
        trx = await conn.fetchrow("SELECT * FROM transactions WHERE id = $1;", trx_id)
        if not trx or str(trx["user_id"]) != user_id:
            raise HTTPException(status_code=404, detail=f"Transaction {trx_id} not found")

        if trx["status"] == TransactionStatus.COMPLETED:
            subscription = await conn.fetchrow("SELECT * FROM user_subscriptions WHERE user_id = $1;", user_id)
            if subscription:
                return subscription
            raise HTTPException(status_code=404, detail=f"Failed to find subscription for user {user_id}")
        else:
            return trx


async def purchase_from_user_balance(user_id):
    async with get_pool().acquire() as conn:
        price = get_price_by_months(1)

        subscription = await conn.fetchrow("SELECT * FROM user_subscriptions WHERE user_id = $1;", user_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Failed to find subscription for purchase")

        async with conn.transaction():
            insert_transaction_query = "INSERT INTO transactions (external_id, user_id, subscription_id, amount, status, payment, recurrent) VALUES ($1, $2, $3, $4, $5, $6, False) RETURNING *;"
            result = await conn.fetchrow(insert_transaction_query, uuid.UUID(int=0), user_id, subscription["id"], 4900, TransactionStatus.COMPLETED, TransactionPayment.BALANCE)
            if result:
                await _update_user_balance(conn, user_id, -price)
                prolong_subscription_query = """
                    UPDATE user_subscriptions SET subscription_ends_at = CASE
                        WHEN subscription_ends_at > CURRENT_TIMESTAMP
                             THEN subscription_ends_at + INTERVAL '1 month'
                        ELSE CURRENT_TIMESTAMP + INTERVAL '1 month'
                    END WHERE id = $1 RETURNING *
                    """
                result = await conn.fetchrow(prolong_subscription_query, subscription["id"])

            if result:
                await _inform_user_prolong(user_id)
                users_cache.pop(user_id, None)
                return result

        raise Exception("Failed to create subscription")


async def fetch_recurrency_by_user_id(user_id):
    async with get_pool().acquire() as conn:
        result = await conn.fetch("SELECT id, created_at FROM transactions WHERE user_id = $1 AND recurrent IS TRUE LIMIT 1", user_id)
        return result if result else []


async def disable_recurrency_for_user(user_id):
    async with get_pool().acquire() as conn:
        # subscriptions could be more suitable but multiple external_id or payment is possible issue-moment
        active_transactions = await conn.fetch("SELECT * FROM transactions WHERE user_id = $1 AND status = 'completed' AND recurrent IS TRUE;", user_id)
        active_transactions = active_transactions if active_transactions else []

        robo_ids = []
        lava_trx = []

        for trx in active_transactions:
            if trx["payment"] == TransactionPayment.ROBOKASSA:
                robo_ids.append(trx["id"])
            elif trx["payment"] == TransactionPayment.LAVA:
                lava_trx.append(trx)

        tasks = [lava.disable_recurrency_for_user(lava_trx)]
        results = await asyncio.gather(*tasks)

        final_result = {key: [item for result in results for item in result.get(key, [])] for key in ("success", "failed")}
        success_external_ids = [trx["external_id"] for trx in final_result["success"]]

        result = await conn.fetch("UPDATE transactions SET recurrent = FALSE, updated_at = CURRENT_TIMESTAMP WHERE id = ANY($1) OR external_id = ANY($2) RETURNING *;", robo_ids, success_external_ids)
        total_success = len(final_result["success"]) + len(robo_ids)
        if result:
            logger.debug(f"Disable recurring for user finished with {total_success} success and {len(final_result['failed'])} failed transactions, marked")
        else:
            logger.debug(f"Disable recurring for user finished with {total_success} success and {len(final_result['failed'])} failed transactions, not marked")


async def unsubscribed_daily_notification():
    await _process_unsubscribed(_notify_unsubscribed_daily)


async def _notify_unsubscribed_daily(subscription):
    user_id = subscription["user_id"]
    limits = get_user_notification_limits(user_id)  # random
    await push_notification_with_payload(user_id, NotificationType.UNSUBSCRIBED_DAILY, {"found_total": limits})


async def check_unsubscribed():
    await asyncio.sleep(600)
    while True:
        try:
            await _process_unsubscribed(_notify_unsubscribed)
        except Exception as e:
            logger.error(f"Failed to check unsubscribed: {e}")
        await asyncio.sleep(600)


async def _notify_unsubscribed(subscription):
    if not subscription["subscription_ends_at"]:
        await push_notification_with_payload(subscription["user_id"], NotificationType.TRIAL_ENDED, {"subscription": subscription})
    else:
        await push_notification_with_payload(subscription["user_id"], NotificationType.UNSUBSCRIBED, {"subscription": subscription})


async def _process_unsubscribed(func):
    processed = []
    while True:
        subscription_id = None
        async with get_pool().acquire() as conn:
            try:
                async with conn.transaction():
                    search_query = """
                        SELECT * FROM user_subscriptions 
                        WHERE ((subscription_ends_at IS NOT NULL AND subscription_ends_at <= CURRENT_TIMESTAMP) OR
                        (subscription_ends_at IS NULL AND trial_ends_at IS NOT NULL AND trial_ends_at <= CURRENT_TIMESTAMP))
                        AND NOT (id = ANY($1::uuid[])) 
                        FOR UPDATE SKIP LOCKED LIMIT 1
                        """
                    subscription = await conn.fetchrow(search_query, processed)
                    if not subscription:
                        return

                    subscription_id = subscription["id"]
                    processed.append(subscription_id)

                    await func(subscription)
            except Exception as e:
                if subscription_id:
                    logger.error(f"Failed to process ended subscription {subscription_id}: {e}")
                else:
                    logger.error(f"Failed to select ended subscription: {e}")
        await asyncio.sleep(1)


async def check_transactions():
    await asyncio.sleep(600)
    while True:
        try:
            await _check_transactions()
        except Exception as e:
            logger.error(f"Failed to check pending transactions: {e}")
        await asyncio.sleep(600)


async def _check_transactions():
    processed = []
    while True:
        trx_id = None
        async with get_pool().acquire() as conn:
            try:
                async with conn.transaction():
                    search_query = """
                        SELECT * FROM transactions 
                        WHERE status = 'pending' AND created_at < CURRENT_TIMESTAMP - INTERVAL '1 hour' AND NOT (id = ANY($1::uuid[])) 
                        FOR UPDATE SKIP LOCKED LIMIT 1
                        """
                    trx = await conn.fetchrow(search_query, processed)
                    if not trx:
                        return

                    trx_id = trx["id"]
                    processed.append(trx_id)

                    new_status = trx["status"]
                    if trx["payment"] == TransactionPayment.ROBOKASSA:
                        new_status = await robo.fetch_transaction_status(trx["number"])
                    elif trx["payment"] == TransactionPayment.LAVA:
                        new_status = await lava.fetch_transaction_status(trx["external_id"])
                    elif trx["payment"] == TransactionPayment.ALPHA:
                        new_status = await alpha.fetch_order_status(trx["external_id"])

                    if new_status == TransactionStatus.PENDING:
                        now = datetime.now(trx["updated_at"].tzinfo)
                        if trx["updated_at"] < (now - timedelta(hours=1)):
                            new_status = TransactionStatus.TIMEOUT

                    if trx["status"] != new_status:
                        logger.error(f"Check is moving transaction {trx_id} to {new_status} status")
                        async with conn.transaction():
                            result = await conn.fetchrow("UPDATE transactions SET status = $3, updated_at = CURRENT_TIMESTAMP WHERE id = $1 AND status = $2 RETURNING id;", trx_id, trx["status"], new_status)
                            if result:
                                if new_status == TransactionStatus.COMPLETED and trx["payment"] != TransactionPayment.BALANCE:
                                    revenue_total.inc(trx["amount"])
                                    payments_completed_total.labels(user_id=str(trx["user_id"])).inc()
                                elif new_status == TransactionStatus.FAILED:
                                    asyncio.create_task(_inform_user_purchase_failed(trx["user_id"]))

                                logger.debug(f"Transaction {trx_id} updated to status: {new_status}")
                            else:
                                logger.warning(f"Transaction {trx_id} already has a new status {new_status}")
            except Exception as e:
                if trx_id:
                    logger.error(f"Failed to process pending transaction {trx_id}: {e}")
                else:
                    logger.error(f"Failed to select pending transaction: {e}")
        await asyncio.sleep(1)


async def robo_recurrency():
    while True:
        try:
            await _robo_recurrency()
        except Exception as e:
            logger.error(f"Failed to check pending transactions: {e}")
        await asyncio.sleep(3600)


async def _robo_recurrency():
    processed = []
    while True:
        trx_id = None
        async with get_pool().acquire() as conn:
            try:
                search_query = """
                    SELECT t.* FROM transactions t
                    INNER JOIN user_subscriptions us ON t.subscription_id = us.id AND us.subscription_ends_at <= CURRENT_TIMESTAMP + INTERVAL '1 day'
                    WHERE t.recurrent IS TRUE AND t.status = 'completed' AND NOT (t.id = ANY($1::uuid[]));
                    """
                trx = await conn.fetchrow(search_query, processed)
                if not trx:
                    return

                trx_id = trx["id"]
                processed.append(trx_id)

                if trx["payment"] != TransactionPayment.ROBOKASSA:
                    continue

                logger.info(f"Processing recurring {trx['payment']} transaction {trx_id} for subscription {trx['subscription_id']}")
                insert_transaction_query = "INSERT INTO transactions (external_id, user_id, subscription_id, amount, recurrent, payment, status) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *;"
                new_transaction = await conn.fetchrow(
                    insert_transaction_query, uuid.UUID(int=0), trx["user_id"], trx["subscription_id"], trx["amount"], False, TransactionPayment.ROBOKASSA, TransactionStatus.PENDING
                )
                try:
                    await robo.init_recurrent_purchase(trx, new_transaction)
                except Exception as e:
                    logger.warning(f"Failed to process robokassa recurrency for {new_transaction["id"]} transaction: {e}")
                    updated = await conn.fetchrow("UPDATE transactions SET status = 'failed', updated_at = CURRENT_TIMESTAMP WHERE id = $1 RETURNING *", new_transaction["id"])
                    if not updated:
                        logger.error(f"Failed to mark recurring transaction {new_transaction['id']} as failed due to: {e}")
            except Exception as e:
                if trx_id:
                    logger.error(f"Failed to process recurring transaction {trx_id}: {e}")
                else:
                    logger.error(f"Failed to select recurring transaction: {e}")
        await asyncio.sleep(1)


async def handle_lava_webhook(webhook: SubscriptionWebhook) -> None:
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
                    select_query = """
                                   SELECT s.id AS subscription_id, s.user_id, t.id AS trx_id
                                   FROM transactions t
                                            INNER JOIN user_subscriptions s ON s.id = t.subscription_id
                                   WHERE t.external_id = $1
                                   LIMIT 1
                                   """
                    info = await conn.fetchrow(select_query, webhook.id)
                    if info:
                        logger.error(f"SUBSCRIPTION CANCELLED id:{info['subscription_id']} trx_id:{info['trx_id']}|{webhook.id} user_id: {info['user_id']}")
                    else:
                        raise IgnoreWebhookException(f"No transactions found for cancelled subscription {webhook.id} ")
                elif webhook.status == WebhookStatus.COMPLETED:
                    trx = await _update_transaction_status(conn, webhook)
                    await _prolong_subscription_or_balance(conn, trx["subscription_id"], webhook.amount, trx["user_id"])
                elif webhook.status == WebhookStatus.COMPLETED_NEW:
                    trx = await _insert_recurring_transaction(conn, webhook, TransactionStatus.COMPLETED)
                    await _prolong_subscription_or_balance(conn, trx["subscription_id"], webhook.amount, trx["user_id"])
                else:
                    raise ValueError(f"Unexpected webhook status {webhook.status}")
    except IgnoreWebhookException as e:
        logger.warning(f"Suppressed {webhook.payment} webhook: {e}")
    except Exception as e:
        logger.warning(f"Failed to process {webhook.payment} webhook: {e}")
        raise Exception(f"Failed to process {webhook.payment} webhook") from e


async def _insert_recurring_transaction(conn: asyncpg.Connection, webhook: SubscriptionWebhook, status: TransactionStatus) -> Record:
    try:
        query = """
                INSERT INTO transactions (external_id, user_id, subscription_id, amount, payment, status, payment_timestamp)
                SELECT $1, t.user_id, t.subscription_id, $2, $3, $4, $5
                FROM transactions t
                WHERE t.external_id = $1
                LIMIT 1
                RETURNING id, user_id
                """
        trx = await conn.fetchrow(query, webhook.id, webhook.amount, webhook.payment, status, webhook.payment_timestamp)

        if trx:
            logger.debug(f"Recurring transaction {trx['id']}|{webhook.id} inserted with {status} status")
            return trx
        else:
            raise IgnoreWebhookException(f"No transactions {webhook.id} found or insert failed")
    except asyncpg.exceptions.UniqueViolationError:
        logger.info(f"Ignoring duplicate {webhook.payment} webhook {webhook.id} {webhook.payment_timestamp}")
        raise IgnoreWebhookException("Webhook already processed")


async def _update_transaction_status(conn: asyncpg.Connection, webhook: SubscriptionWebhook) -> Record:
    try:
        query = """
                UPDATE transactions t
                SET status            = $3,
                    updated_at        = CURRENT_TIMESTAMP,
                    payment_timestamp = COALESCE(payment_timestamp, $4)
                FROM (SELECT id
                      FROM transactions
                      WHERE external_id = $1
                        AND amount = $2
                        AND status = 'pending'
                      ORDER BY created_at DESC FOR UPDATE SKIP LOCKED
                      LIMIT 1) it
                WHERE t.id = it.id
                RETURNING t.id, t.user_id
                """
        trx = await conn.fetchrow(query, webhook.id, webhook.amount, webhook.status, webhook.payment_timestamp)

        if trx:
            logger.debug(f"Transaction {trx['id']}|{webhook.id} updated to status: {webhook.status}")
            return trx
        else:
            raise IgnoreWebhookException(f"No pending transactions {webhook.id} for {webhook.amount}")
    except asyncpg.exceptions.UniqueViolationError:
        logger.info(f"Ignoring duplicate {webhook.payment} webhook {webhook.id} {webhook.payment_timestamp}")
        raise IgnoreWebhookException("Webhook already processed")


async def _prolong_subscription_or_balance(conn: asyncpg.Connection, subscription_id: uuid.UUID, price: int, user_id):
    try:
        await _prolong_subscription(conn, subscription_id, price)
    except ValueError as e:
        logger.warning(f"Failed to prolong subscription, updating balance: {e}")
        await _update_user_balance(conn, user_id, price)


async def _prolong_subscription(conn: asyncpg.Connection, subscription_id: uuid.UUID, price: int):
    months = get_months_by_price(price)
    query = f"""
        UPDATE user_subscriptions SET subscription_ends_at = CASE
            WHEN subscription_ends_at > CURRENT_TIMESTAMP
                 THEN subscription_ends_at + INTERVAL '{months} month'
            ELSE CURRENT_TIMESTAMP + INTERVAL '{months} month'
        END WHERE id = $1 RETURNING *
    """
    result = await conn.fetchrow(query, subscription_id)
    if result:
        return result
    raise Exception(f"Failed to prolong subscription {subscription_id} for {months} months")


async def _update_user_balance(conn: asyncpg.Connection, user_id: uuid.UUID, amount: int) -> None:
    row = await conn.fetchrow("UPDATE users SET balance = balance + $2 WHERE id = $1 RETURNING balance - $2 AS old_balance, balance AS new_balance;", user_id, amount)
    if row:
        logger.debug(f"User {user_id} balance updated from {row['old_balance']} to {row['new_balance']}")
    else:
        raise Exception(f"Failed to update user {user_id} balance for {amount}")


async def _inform_user_purchase_failed(user_id):
    await push_notification_with_payload(user_id, NotificationType.PURCHASE_FAILED, {"must_core": True})


async def _inform_user_prolong(user_id):
    async with get_pool().acquire() as conn:
        first = not await conn.fetchval("SELECT EXISTS (SELECT 1 FROM transactions WHERE user_id = $1 AND status = 'completed' OFFSET 1);", user_id)
        await push_notification_with_payload(user_id, NotificationType.PURCHASE_DONE, {"first": first, "must_core": True, "user_id": user_id})
