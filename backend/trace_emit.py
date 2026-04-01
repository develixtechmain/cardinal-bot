import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

import aio_pika

logger = logging.getLogger(__name__)

TRACE_QUEUE = "trace_events"

_connection: aio_pika.RobustConnection | None = None
_channel: aio_pika.RobustChannel | None = None


def trace_enabled() -> bool:
    return bool(os.environ.get("RABBITMQ_PASS"))


def _rabbitmq_url() -> str:
    host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
    port = os.environ.get("RABBITMQ_PORT", "5672")
    user = os.environ.get("RABBITMQ_USER", "cardinal")
    password = os.environ.get("RABBITMQ_PASS", "")
    vhost = os.environ.get("RABBITMQ_VHOST", "/")
    return f"amqp://{user}:{password}@{host}:{port}{vhost}"


async def _ensure_channel() -> aio_pika.RobustChannel:
    global _connection, _channel
    if _connection is not None and _connection.is_closed:
        logger.warning("trace RabbitMQ connection lost, resetting")
        _connection = None
        _channel = None
    if _channel is None or _channel.is_closed:
        url = _rabbitmq_url()
        safe_url = url.replace(os.environ.get("RABBITMQ_PASS", ""), "***")
        logger.info("trace: connecting to RabbitMQ %s", safe_url)
        _connection = await aio_pika.connect_robust(url)
        _channel = await _connection.channel()
        await _channel.declare_queue(TRACE_QUEUE, durable=True)
        logger.info("trace: channel ready, queue '%s' declared", TRACE_QUEUE)
    return _channel


async def emit(
    correlation_id: str,
    service: str,
    stage: str,
    status: str,
    detail: Optional[dict[str, Any]] = None,
    *,
    recommendation_id: Optional[UUID] = None,
    source_chat_id: Optional[str] = None,
    source_message_id: Optional[int] = None,
    source_text: Optional[str] = None,
    duration_ms: Optional[int] = None,
) -> None:
    if not trace_enabled():
        logger.debug("trace: disabled (RABBITMQ_PASS not set)")
        return
    body: dict[str, Any] = {
        "correlation_id": correlation_id,
        "service": service,
        "stage": stage,
        "status": status,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "detail": detail or {},
    }
    if recommendation_id is not None:
        body["recommendation_id"] = str(recommendation_id)
    if source_chat_id is not None:
        body["source_chat_id"] = source_chat_id
    if source_message_id is not None:
        body["source_message_id"] = source_message_id
    if source_text is not None:
        body["source_text"] = source_text
    if duration_ms is not None:
        body["duration_ms"] = duration_ms
    try:
        channel = await _ensure_channel()
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(body).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=TRACE_QUEUE,
        )
        logger.debug("trace: published %s/%s/%s cid=%s", service, stage, status, correlation_id)
    except Exception as e:
        logger.warning("trace emit failed: %s", e, exc_info=True)
