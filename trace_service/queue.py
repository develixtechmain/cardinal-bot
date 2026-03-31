import asyncio
import json
import logging
import os

import aio_pika

logger = logging.getLogger(__name__)

QUEUE_NAME = "trace_events"

_connection: aio_pika.RobustConnection | None = None
_publish_channel: aio_pika.RobustChannel | None = None


def _rabbitmq_url() -> str:
    host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
    port = os.environ.get("RABBITMQ_PORT", "5672")
    user = os.environ.get("RABBITMQ_USER", "cardinal")
    password = os.environ.get("RABBITMQ_PASS", "")
    vhost = os.environ.get("RABBITMQ_VHOST", "/")
    return f"amqp://{user}:{password}@{host}:{port}{vhost}"


async def init_queue() -> None:
    global _connection, _publish_channel
    _connection = await aio_pika.connect_robust(_rabbitmq_url())
    _publish_channel = await _connection.channel()
    await _publish_channel.declare_queue(QUEUE_NAME, durable=True)
    logger.info("trace_service: queue ready")


async def close_queue() -> None:
    global _connection
    if _connection:
        await _connection.close()
        _connection = None


async def publish(payload: dict) -> None:
    if _publish_channel is None:
        raise RuntimeError("Queue not initialized")
    await _publish_channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(payload).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key=QUEUE_NAME,
    )


async def run_worker(ingest_fn) -> None:
    """Consume trace events from the queue and write them to DB via ingest_fn."""
    conn = await aio_pika.connect_robust(_rabbitmq_url())
    channel = await conn.channel()
    await channel.set_qos(prefetch_count=20)
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)

    logger.info("trace_service: worker started, consuming from '%s'", QUEUE_NAME)

    async with queue.iterator() as it:
        async for message in it:
            async with message.process(requeue=True):
                try:
                    body = json.loads(message.body)
                    await ingest_fn(body)
                except Exception as e:
                    logger.warning("trace worker: failed to ingest event: %s", e)
                    raise  # triggers requeue once, then dead-letter if configured
