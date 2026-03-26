import asyncio
import json
import logging
import os
from datetime import datetime, timedelta

import aio_pika
from aio_pika.abc import AbstractRobustChannel, AbstractRobustQueue
from dotenv import load_dotenv
import ai
import core
import db
import deepseek
import embedding
from ai import check_lead
from deepseek import check_relevance, is_relevant
from embedding import search_candidates
from utils import validate_env

load_dotenv()

rabbitmq_connection: aio_pika.RobustConnection
rabbitmq_channel: AbstractRobustChannel
rabbitmq_queue: AbstractRobustQueue
queue_name = "tg_queue"

logger = logging.getLogger(__name__)


async def process_message(body, message: aio_pika.abc.AbstractIncomingMessage):
    try:
        await _process_message(body)
        await message.ack()
    except Exception as e:
        logger.warning(f"Failed to process message: {e}")
        await message.reject(requeue=False)


async def _process_message(body: bytes):
    try:
        message = json.loads(body)
    except Exception as e:
        raise Exception(f"Failed to read message: {e}")

    logger.debug(f"Received message: {message['text']}")

    search_response = await search_candidates(message['text'])
    if not search_response:
        return

    is_lead = await check_lead(message)
    if not is_lead:
        return

    await db.save_in_clickhouse(message)

    try:
        selected_candidate = await select_candidate(search_response)
    except Exception as e:
        raise Exception(f"Failed to find candidate for {message['message_id']} from {message['chat_id']}: {e}")

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


async def save_recommendation(candidate, recommendation):
    try:
        user = await db.fetch_user_by_id(candidate["userId"])
        recommendation_id = await db.save_recommendation(user, candidate['taskId'], recommendation)
        await embedding.confirm_recommendation(recommendation_id, candidate)
        await core.send_recommendation_to_user(recommendation, candidate)
    except Exception as e:
        raise Exception(f"Failed to recommend {recommendation['message_id']} from {recommendation['chat_id']} to user {candidate['userId']}: {e}")


async def select_candidate(candidates):
    now = datetime.now()
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
        raise Exception(f"Failed to fetch user stats: {e}")

    if stats["last_recommendation_at"]:
        time_since_last = now - stats["last_recommendation_at"]
        time_factor = max(0, 1 - (time_since_last.total_seconds() / 3600))
    else:
        time_factor = 0

    loyalty_bonus = min(0.1, stats["total_recommendations"] / 10000)
    candidate["rating"] = (
            0.3 * (1 / (stats["recent_recommendations"] + 1)) +
            0.3 * candidate["score"] +
            0.25 * (1 - time_factor) +
            0.15 * loyalty_bonus
    )


async def init_rabbitmq():
    global rabbitmq_channel, rabbitmq_connection, rabbitmq_queue

    validate_env("RABBITMQ_PASS")

    host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
    port = os.environ.get("RABBITMQ_PORT", 5672)
    vhost = os.environ.get("RABBITMQ_VHOST", "/")
    user = os.environ.get("RABBITMQ_USER", "cardinal")
    password = os.environ["RABBITMQ_PASS"]

    rabbitmq_connection = await aio_pika.connect_robust(f"amqp://{user}:{password}@{host}:{port}{vhost}")
    rabbitmq_channel = await rabbitmq_connection.channel()
    rabbitmq_queue = await rabbitmq_channel.declare_queue(queue_name, durable=True)


async def main():
    global rabbitmq_queue

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    logger.info("Listener startup initiated.")

    try:
        await init_rabbitmq()
        logger.info(f"Connected to RabbitMQ.")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        return

    try:
        await db.init_click()
        logger.info(f"Connected to ClickHouse.")
    except Exception as e:
        logger.error(f"Failed to connect to ClickHouse: {e}")
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
        logger.error(f"Failed to configure: {e}")
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
                asyncio.create_task(process_message(message.body, message))
    finally:
        await db.disconnect()
        await rabbitmq_connection.close()
        logger.info("RabbitMQ connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
