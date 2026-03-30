import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

import aio_pika
import redis.asyncio as redis
import xxhash
from aio_pika.abc import AbstractRobustChannel, AbstractRobustQueue
from dotenv import load_dotenv

import ai
import core
import db
import deepseek
import embedding
import handlers
from ai import check_lead
from deepseek import check_relevance, is_relevant
from embedding import search_candidates
from handlers import HANDLERS, ID_HANDLERS
from trace_emit import emit as trace_emit
from utils import validate_env

load_dotenv()

redis_ttl = 86400
redis_client: redis.Redis

rabbitmq_connection: aio_pika.RobustConnection
rabbitmq_consume_channel: AbstractRobustChannel
rabbitmq_queue: AbstractRobustQueue
queue_name = "tg_queue"

queue_tasks: asyncio.Semaphore

logger = logging.getLogger(__name__)

spam_abuse_suffixes = ("Интересно? Пиши", "Заинтересовало? Пиши", "Пиши")


async def process_message(body, message: aio_pika.abc.AbstractIncomingMessage):
    try:
        await _process_message(body)
        await message.ack()
    except Exception as e:
        logger.warning(f"Failed to process message: {e}")
        await message.reject(requeue=False)


total_messages = 0
total_skipped = 0
total_grouped = 0
total_from_group = 0
total_found = 0
total_not_found = 0
total_standardized = 0
total_new = 0
total_refresh = 0
total_scam = 0
total_processed = 0


def log_process():
    logger.info(
        f"\nTotal: {total_messages} | {total_messages - total_skipped - total_refresh} | {total_found - total_scam}\n"
        f"Processed: {total_processed}, {total_from_group} from {total_grouped} grouped\n"
        f"Skipped: {total_skipped} + refresh: {total_refresh} = {total_skipped + total_refresh} with {total_standardized} standardized\n"
        f"New: {total_new}: found: {total_found}, not found: {total_not_found}, scam: {total_scam}"
    )


def _trace_ids(message: dict) -> tuple[str, str | None, int | None]:
    cid = message.get("correlation_id")
    if not cid:
        cid = str(uuid.uuid4())
        message["correlation_id"] = cid
    chat_id = str(message.get("chat_id", "")) or None
    mid = message.get("message_id")
    try:
        mid_int = int(mid) if mid is not None else None
    except (TypeError, ValueError):
        mid_int = None
    return cid, chat_id, mid_int


async def _process_message(body: bytes):
    global total_messages, total_skipped, total_grouped, total_from_group, total_found, total_not_found, total_standardized, total_new, total_refresh, total_scam, total_processed

    try:
        message = json.loads(body)
    except Exception as e:
        raise Exception(f"Failed to read message") from e

    had_correlation = bool(message.get("correlation_id"))
    correlation_id, source_chat_id, source_message_id = _trace_ids(message)
    consume_detail = {"chat_handler_processed": message.get("chat_handler_processed", False)}
    if not had_correlation:
        consume_detail["legacy_missing_correlation"] = True
    await trace_emit(
        correlation_id,
        "message_processor",
        "consume",
        "ok",
        consume_detail,
        source_chat_id=source_chat_id,
        source_message_id=source_message_id,
    )

    message_text = message["text"]

    total_messages += 1
    if message.get("chat_handler_processed"):
        logger.info(f"Received part message:\n{message_text}")
        total_from_group += 1

    if (
        message_text.startswith("Message from user")
        or message_text.endswith("been kicked from the chat because this user is in spam list")
        or message_text.endswith("has been removed because it matches a filter mention (???)")
    ):
        total_skipped += 1
        await trace_emit(
            correlation_id,
            "message_processor",
            "filter",
            "skipped",
            {"reason": "system_or_spam_pattern"},
            source_chat_id=source_chat_id,
            source_message_id=source_message_id,
        )
        log_process()
        return

    last_line_starts_at = message_text.rfind("\n")
    if last_line_starts_at == -1:
        last_line_starts_at = 0
    else:
        last_line_starts_at += 1

    last_line = message_text[last_line_starts_at:]
    for prefix in spam_abuse_suffixes:
        if last_line.startswith(prefix):
            mentions = 0
            for word in last_line.split():
                if word.startswith("@"):
                    mentions += 1
                    if mentions > 1:
                        break
            if mentions > 1:
                message_text = message_text[:last_line_starts_at]
                total_standardized += 1

    try:
        message_key = xxhash.xxh3_64_intdigest(message_text).to_bytes(8)
        if await redis_client.exists(message_key):
            log_process()
            await redis_client.expire(message_key, redis_ttl)
            total_refresh += 1
            await trace_emit(
                correlation_id,
                "message_processor",
                "redis_dedup",
                "filtered",
                {},
                source_chat_id=source_chat_id,
                source_message_id=source_message_id,
            )
            return
        else:
            total_new += 1
            logger.debug(f"Key {message_key} set from {message_text}")
            await redis_client.set(message_key, b"", ex=redis_ttl)
    except Exception as e:
        logger.warning(f"Failed to check for duplicate: ", exc_info=e)

    if not message.get("chat_handler_processed"):
        for key_handlers, key in [(HANDLERS, message["chat_username"]), (ID_HANDLERS, message["chat_id"])]:
            handler = key_handlers.get(key)
            if handler and await handler(message):
                total_grouped += 1
                await trace_emit(
                    correlation_id,
                    "message_processor",
                    "handler_routed",
                    "ok",
                    {"handler": "chat_split_or_route"},
                    source_chat_id=source_chat_id,
                    source_message_id=source_message_id,
                )
                return

    logger.log(0, f"Received message:\n{message_text}")

    search_response = await search_candidates(message_text)
    if not search_response:
        total_not_found += 1
        await trace_emit(
            correlation_id,
            "message_processor",
            "embedding_search",
            "filtered",
            {"candidates": 0},
            source_chat_id=source_chat_id,
            source_message_id=source_message_id,
        )
        log_process()
        return

    total_found += 1
    await trace_emit(
        correlation_id,
        "message_processor",
        "embedding_search",
        "ok",
        {"candidates": len(search_response)},
        source_chat_id=source_chat_id,
        source_message_id=source_message_id,
    )
    is_lead = await check_lead(message)
    if not is_lead:
        total_scam += 1
        await trace_emit(
            correlation_id,
            "message_processor",
            "lead_check",
            "filtered",
            {},
            source_chat_id=source_chat_id,
            source_message_id=source_message_id,
        )
        log_process()
        return

    await db.save_message(message)
    await trace_emit(
        correlation_id,
        "message_processor",
        "db_save_message",
        "ok",
        {},
        source_chat_id=source_chat_id,
        source_message_id=source_message_id,
    )

    try:
        selected_candidate = await select_candidate(search_response)
    except Exception as e:
        raise Exception(f"Failed to find candidate for {message['message_id']} from {message['chat_id']}") from e

    rating = selected_candidate["rating"] * 0.9

    tasks = []
    for candidate in search_response:
        if candidate["rating"] > rating:
            logger.info(f"User {candidate['userId']} selected for recommendation.")
            if candidate["stats"]["recent_recommendations"] >= 33:
                logger.info(f"User {candidate['userId']} skipped recommendation due to daily limit.")
                continue

            user_task = await db.fetch_user_task(candidate["taskId"])
            if not user_task:
                logger.warning(f"Task {candidate['taskId']} not found, skipping relevance check.")
                continue

            tags = user_task["tags"] if isinstance(user_task["tags"], list) else json.loads(user_task["tags"])
            relevance = await check_relevance(message["text"], user_task["title"], tags)

            if not is_relevant(relevance):
                logger.info(
                    f"User {candidate['userId']} skipped: low relevance "
                    f"(confidence={relevance['confidence']}, reason={relevance['reasoning']})"
                )
                continue

            if relevance:
                logger.info(
                    f"User {candidate['userId']} passed relevance check "
                    f"(confidence={relevance['confidence']})"
                )

            tasks.append(save_recommendation(candidate, message))

    await asyncio.gather(*tasks)
    total_processed += 1
    await trace_emit(
        correlation_id,
        "message_processor",
        "recommendations_batch",
        "ok",
        {"tasks": len(tasks)},
        source_chat_id=source_chat_id,
        source_message_id=source_message_id,
    )
    log_process()


async def save_recommendation(candidate, message):
    correlation_id = message.get("correlation_id") or str(uuid.uuid4())
    source_chat_id = str(message.get("chat_id", "")) or None
    try:
        mid = int(message["message_id"])
    except (TypeError, ValueError, KeyError):
        mid = None
    try:
        user = await db.fetch_user_by_id(candidate["userId"])
        recommendation_id = await db.save_recommendation(user, candidate["taskId"], message)
        await embedding.confirm_recommendation(recommendation_id, candidate)
        await core.send_recommendation_to_user(message, candidate, recommendation_id)
        await trace_emit(
            correlation_id,
            "message_processor",
            "http_recommendation",
            "ok",
            {"user_id": str(candidate["userId"]), "task_id": str(candidate["taskId"])},
            recommendation_id=recommendation_id,
            source_chat_id=source_chat_id,
            source_message_id=mid,
        )
    except Exception as e:
        await trace_emit(
            correlation_id,
            "message_processor",
            "http_recommendation",
            "error",
            {"user_id": str(candidate.get("userId")), "error": str(e)[:500]},
            source_chat_id=source_chat_id,
            source_message_id=mid,
        )
        raise Exception(f"Failed to recommend {message['message_id']} from {message['chat_id']} to user {candidate['userId']}") from e


async def select_candidate(candidates):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)
    selected_candidate = None

    tasks = []
    for candidate in candidates:
        tasks.append(calculate_rating(now, cutoff, candidate))

    await asyncio.gather(*tasks)

    for candidate in candidates:
        if selected_candidate is None or candidate["rating"] > selected_candidate["rating"]:
            selected_candidate = candidate

    return selected_candidate


async def calculate_rating(now, cutoff, candidate):
    try:
        stats = await db.get_user_stats(candidate["userId"], cutoff)
        candidate["stats"] = stats
    except Exception as e:
        raise Exception(f"Failed to fetch user stats") from e

    if stats["last_recommendation_at"]:
        time_since_last = now - stats["last_recommendation_at"]
        time_factor = max(0, 1 - (time_since_last.total_seconds() / 3600))
    else:
        time_factor = 0

    loyalty_bonus = min(0.1, stats["total_recommendations"] / 10000)

    recent_rating = 0.3 * (1 / (stats["recent_recommendations"] + 1))
    score_rating = 0.3 * candidate["score"]
    time_rating = 0.25 * (1 - time_factor)
    loyalty_rating = 0.15 * loyalty_bonus
    candidate["rating"] = recent_rating + score_rating + time_rating + loyalty_rating


async def init_redis():
    global redis_client

    validate_env("REDIS_PASSWORD")

    # fmt: off
    redis_client = redis.Redis(
        host=os.environ.get("REDIS_HOST", "redis"),
        port=int(os.environ.get("REDIS_PORT", 6379)),
        password=os.environ["REDIS_PASSWORD"],
        db=0, max_connections=20, decode_responses=False
    )
    # fmt: on


async def init_rabbitmq():
    global rabbitmq_consume_channel, rabbitmq_connection, rabbitmq_queue, queue_tasks

    validate_env("RABBITMQ_PASS")

    host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
    port = os.environ.get("RABBITMQ_PORT", 5672)
    vhost = os.environ.get("RABBITMQ_VHOST", "/")
    user = os.environ.get("RABBITMQ_USER", "cardinal")
    password = os.environ["RABBITMQ_PASS"]

    tasks = int(os.environ.get("QUEUE_TASKS", 50))
    queue_tasks = asyncio.Semaphore(tasks)

    rabbitmq_connection = await aio_pika.connect_robust(f"amqp://{user}:{password}@{host}:{port}{vhost}")
    rabbitmq_consume_channel = await rabbitmq_connection.channel(publisher_confirms=False)
    await rabbitmq_consume_channel.set_qos(prefetch_count=tasks)
    rabbitmq_queue = await rabbitmq_consume_channel.declare_queue(queue_name, durable=True)

    rabbitmq_publish_channel = await rabbitmq_connection.channel(publisher_confirms=True)
    handlers.init_handlers(rabbitmq_publish_channel, queue_name)


async def main():
    global rabbitmq_queue

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    for package in ("httpx", "httpcore", "aiormq.connection", "openai._base_client", "langsmith.client"):
        logging.getLogger(package).setLevel(logging.INFO)

    logger.info("Listener startup initiated.")

    try:
        await init_redis()
        logger.info(f"Connected to Redis.")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return

    try:
        await init_rabbitmq()
        logger.info(f"Connected to RabbitMQ.")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        return

    try:
        await db.init_postgresql()
        logger.info(f"Connected to PostgreSQL.")
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        return

    try:
        await ai.init_llm()
        logger.info(f"LLM initiated.")
    except Exception as e:
        logger.error(f"Failed init LLM : {e}")
        return

    try:
        embedding.init_embedding()
    except Exception as e:
        logger.error(f"Failed to configure embeddings: {e}")
        return

    try:
        core.init_core()
    except Exception as e:
        logger.error(f"Failed to configure backend: {e}")
        return

    try:
        deepseek.init_deepseek()
        logger.info("DeepSeek initiated.")
    except Exception as e:
        logger.error(f"Failed to init DeepSeek: {e}")
        return

    logger.info(f"Listener started.")

    try:
        async with rabbitmq_queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with queue_tasks:
                    asyncio.create_task(process_message(message.body, message))
    finally:
        await db.disconnect()
        await rabbitmq_connection.close()
        logger.info("RabbitMQ connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
