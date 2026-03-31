import asyncio
import json
import logging
import os

import aio_pika

from db import close_db, get_pool, init_db
from ingest import ingest_event_pool
from models import TraceEventIngest

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

QUEUE_NAME = "trace_events"
BATCH_SIZE = int(os.environ.get("TRACE_BATCH_SIZE", "50"))
BATCH_TIMEOUT = float(os.environ.get("TRACE_BATCH_TIMEOUT", "2.0"))


def _rabbitmq_url() -> str:
    host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
    port = os.environ.get("RABBITMQ_PORT", "5672")
    user = os.environ.get("RABBITMQ_USER", "cardinal")
    password = os.environ.get("RABBITMQ_PASS", "")
    vhost = os.environ.get("RABBITMQ_VHOST", "/")
    return f"amqp://{user}:{password}@{host}:{port}{vhost}"


async def _flush_batch(batch: list[tuple[aio_pika.IncomingMessage, dict]]) -> None:
    """Write a batch of events to the DB, ack on success, nack on failure."""
    if not batch:
        return
    pool = get_pool()
    succeeded = 0
    for msg, body in batch:
        try:
            event = TraceEventIngest.model_validate(body)
            await ingest_event_pool(pool, event)
            await msg.ack()
            succeeded += 1
        except Exception as e:
            logger.warning("trace ingest failed for %s: %s", body.get("correlation_id", "?"), e)
            await msg.nack(requeue=True)
    logger.debug("batch: %d/%d ingested", succeeded, len(batch))


async def consume() -> None:
    conn = await aio_pika.connect_robust(_rabbitmq_url())
    channel = await conn.channel()
    await channel.set_qos(prefetch_count=BATCH_SIZE)
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)

    logger.info("trace-service: consuming from '%s' (batch=%d, timeout=%.1fs)", QUEUE_NAME, BATCH_SIZE, BATCH_TIMEOUT)

    batch: list[tuple[aio_pika.IncomingMessage, dict]] = []

    async with queue.iterator() as it:
        while True:
            try:
                msg = await asyncio.wait_for(it.__anext__(), timeout=BATCH_TIMEOUT)
                try:
                    body = json.loads(msg.body)
                except Exception:
                    logger.warning("trace-service: bad JSON, dropping message")
                    await msg.ack()
                    continue
                batch.append((msg, body))
                if len(batch) >= BATCH_SIZE:
                    await _flush_batch(batch)
                    batch = []
            except asyncio.TimeoutError:
                if batch:
                    await _flush_batch(batch)
                    batch = []
            except StopAsyncIteration:
                break

    if batch:
        await _flush_batch(batch)


async def main() -> None:
    await init_db()
    logger.info("trace-service: DB ready")
    try:
        await consume()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
