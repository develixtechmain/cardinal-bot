import asyncio
import json
import logging
import re
from functools import partial
from typing import Callable

from aio_pika import Message
from aio_pika.abc import AbstractRobustChannel, DeliveryMode

logger = logging.getLogger(__name__)

_rabbitmq_channel: AbstractRobustChannel | None = None
_queue_name: str | None = None

publish_semaphore = asyncio.Semaphore(20)


async def publish_message(part, part_number):
    async with publish_semaphore:
        try:
            await _rabbitmq_channel.default_exchange.publish(routing_key=_queue_name, message=Message(body=json.dumps(part).encode(), delivery_mode=DeliveryMode.PERSISTENT))
            logger.info(f"Message {part['message_id']} part {part_number} published")
        except Exception as e:
            logger.error(f"Failed to publish message {part['message_id']} part {part_number}: {str(e)}")


async def process_by_blocks(message, line_prefix: str | None = None, prefix: str | None = None, suffix: str | None = None, prefix_blocks: int = 1, suffix_blocks: int = 1):
    message_text = message["text"]

    raw_blocks = message_text.split("\n\n")

    if prefix:
        if prefix in raw_blocks[0]:
            raw_blocks = raw_blocks[prefix_blocks:]
        else:
            return False

    if line_prefix and not raw_blocks[0].startswith(line_prefix):
        return False

    part_number = 0
    parts = []
    tasks = []
    for i, raw_block in enumerate(raw_blocks):
        if suffix and i == len(raw_blocks) - suffix_blocks:
            suffix_pos = raw_block.find(suffix)
            if suffix_pos != -1:
                raw_block = raw_block[:suffix_pos]

        block_lines = raw_block.splitlines()
        block_lines = [line.strip() for line in block_lines if line.strip()]
        if not block_lines:
            continue

        if line_prefix and not block_lines[0].startswith(line_prefix):
            continue

        username = None
        last_line = block_lines[-1]
        username_pos = last_line.find("@")
        if username_pos != -1:
            end_pos = last_line.find(" ", username_pos)
            if end_pos == -1:
                end_pos = len(last_line)
            username = last_line[username_pos + 1 : end_pos].strip()
            block_lines = block_lines[:-1]

        part = message.copy()
        part.update({"text": "\n".join(block_lines).strip(), "user_username": username, "chat_handler_processed": True})
        part_number += 1
        parts.append(part)
        logger.info(f"Attempting to process part {part['message_id']} with number {part_number}")
        tasks.append(publish_message(part, part_number))
    try:
        await asyncio.gather(*tasks)
        logger.info(f"Message parted:\n{message_text}")
        for i, part in enumerate(parts):
            logger.info(f"Part {i}:\n{part['text']}")

    except Exception as e:
        print(f"Failed to send partial lead to queue: {e}")

    return True


numbered_with_username = re.compile(r"^\d+\.\s*(?P<text>[\s\S]*?)(?:📝\s*)?@(?P<username>[A-Za-z0-9_]+)", re.MULTILINE)


async def process_numbered_with_username(message):
    return _process_with_regex(message, numbered_with_username)


titled_with_username = re.compile(r"^(?:[^\n]*Подборка[^\n]*\n\n)?(?P<text>[\s\S]*?)\nКонтакты:\s*@(?P<username>[A-Za-z0-9_]+)", re.MULTILINE)


async def process_titled_with_username(message):
    return await _process_with_regex(message, titled_with_username)


async def _process_with_regex(message, pattern):
    matches = list(pattern.finditer(message["text"]))
    if not matches:
        return False

    part_number = 0
    parts = []
    tasks = []
    for match in matches:
        part = message.copy()
        part.update({"text": match.group("text").strip(), "user_username": match.group("username"), "chat_handler_processed": True})
        part_number += 1
        parts.append(part)
        logger.info(f"Attempting to process part {part['message_id']} with number {part_number}")
        tasks.append(publish_message(part, part_number))
    try:
        await asyncio.gather(*tasks)
        logger.info(f"Message parted:\n{message['text']}")
        for i, part in enumerate(parts):
            logger.info(f"Part {i}:\n{part['text']}")
    except Exception as e:
        logger.warning(f"Failed to send partial lead to queue: {e}")

    return True


HANDLERS: dict[str, Callable] = {
    "worldeventjob": process_numbered_with_username,
    "rueventjob": process_numbered_with_username,
    "board_axolotl": process_titled_with_username,
    "TRemoters": process_numbered_with_username,
    "designwork_vacansii": partial(process_by_blocks, line_prefix="#"),
    "frilans": partial(process_by_blocks, line_prefix="#", suffix="Размещение вакансий"),
    "searcher_freelance": process_numbered_with_username,
    # "Koteyka_Freelancer": ТУТ КНОПКА НА ЧАТ С БОТОМ
    "mskeventjob": process_numbered_with_username,
}

ID_HANDLERS: dict[int, Callable] = {
    -1001759111893: partial(process_by_blocks, line_prefix="#", suffix="в нашем боте", suffix_blocks=2),  # Удалёночка
    -1001279580013: partial(process_by_blocks, suffix="workodav"),  # Воркодав
}


def init_handlers(channel, queue_name):
    global _rabbitmq_channel, _queue_name
    _rabbitmq_channel = channel
    _queue_name = queue_name
