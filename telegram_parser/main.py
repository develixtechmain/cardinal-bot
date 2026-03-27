import asyncio
import json
import logging
import os
import random
import sys
from functools import partial
from typing import Any, Awaitable, Protocol

import aio_pika
import redis.asyncio as redis
from aio_pika.abc import AbstractRobustChannel
from dotenv import load_dotenv
from pyrogram import Client, errors, filters, idle, session
from pyrogram.errors import InternalServerError, ServiceUnavailable
from pyrogram.handlers import DisconnectHandler, EditedMessageHandler, MessageHandler, RawUpdateHandler
from pyrogram.raw.functions.updates import GetDifference, GetState
from pyrogram.raw.types import (
    Channel,
    UpdateChannelMessageViews,
    UpdateChannelTooLong,
    UpdateChannelUserTyping,
    UpdateChannelWebPage,
    UpdateEditChannelMessage,
    UpdateEditMessage,
    UpdateNewAuthorization,
    UpdateNewChannelMessage,
    UpdateNewMessage,
    UpdatePinnedChannelMessages,
    UpdateStory,
)
from pyrogram.types import InlineKeyboardButton, Message

from buttons import ButtonsHandle, handle_buttons, handle_fast_click_button, handle_fast_id_url_button, handle_fast_url_button, handle_generic_button
from utils import validate_env


class CustomLogger(logging.Logger):
    TRACE_LEVEL = logging.DEBUG - 1
    logging.addLevelName(TRACE_LEVEL, "TRACE")

    def trace(self, message, *args, **kwargs):
        if self.isEnabledFor(self.TRACE_LEVEL):
            self._log(self.TRACE_LEVEL, message, args, **kwargs)


load_dotenv()

rabbitmq_connection: aio_pika.RobustConnection
rabbitmq_channel: AbstractRobustChannel
queue_name = "tg_queue"
queue = asyncio.Queue(maxsize=30000)

rabbitmq_workers = 16
pyrogram_workers = 8

apps: dict[int, Client] = {}

redis_client: redis.Redis
PULL_LIMIT = 50
PULL_INTERVAL = 120  # +- 30
GAP_WARNING_THRESHOLD = 500

logging.setLoggerClass(CustomLogger)
logger: CustomLogger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ButtonsHandler(Protocol):
    def __call__(self, *, app: Client, payload: dict) -> Awaitable[ButtonsHandle]: ...


EXACT_RULES: dict[str, ButtonsHandler] = {
    "ALLW0RK": partial(handle_fast_url_button, fast_name="Написать автору"),
    "DesignHub_Jobs": partial(handle_fast_url_button, fast_name="Написать автору"),
    "Easy_wrk": partial(handle_fast_url_button, fast_name="Написать автору"),
    "lead_hunter_mailing_bot": partial(handle_fast_id_url_button, fast_name="Написать Заказчику"),
    "GetClient": partial(handle_fast_url_button, fast_name="Связаться с автором"),
}

PREFIX_RULES: dict[str, ButtonsHandler] = {
    "GetClient": partial(handle_fast_click_button, fast_click_name="Показать контакты", fast_name="Связаться с автором"),
    "LeadMagnet": partial(handle_fast_url_button, fast_name="Связаться с автором"),
}

DEFAULT_HANDLER = handle_generic_button

SPAM_TEXT_ENDS = ["https://t.me/+OXjqEYTG9Wk1NWI6.", "Купить рекламу в этом чате можно ЗДЕСЬ"]

total_messages = 0
total_send_messages = 0


def loop_exception_handler(_, context):
    exc = context.get("exception")
    if isinstance(exc, (BrokenPipeError, ConnectionResetError, OSError)):
        logging.error("Fatal MTProto transport error, exiting", exc_info=exc)
        sys.exit(1)


asyncio.get_event_loop().set_exception_handler(loop_exception_handler)

_original_invoke = session.Session.invoke


async def invoke_no_storm(self, query, retries=1, timeout=None, sleep_threshold=None):
    try:
        return await _original_invoke(self, query, retries=retries, timeout=timeout, sleep_threshold=sleep_threshold)
    except (OSError, BrokenPipeError) as e:
        logger.warning(f"Retryable {e.__class__.__name__}, retrying once: {e}")
        await asyncio.sleep(1)
        try:
            return await _original_invoke(self, query, retries=0, timeout=timeout, sleep_threshold=sleep_threshold)
        except Exception as retry_e:
            logger.error(f"Failed to retry invoke due to {retry_e.__class__.__name__}: {e} -> {retry_e}")
            sys.exit(1)
    except (InternalServerError, ServiceUnavailable) as e:
        logger.error(f"Critical Telegram error, exiting: {e}", exc_info=True)
        sys.exit(1)


session.Session.invoke = invoke_no_storm


async def disconnect(app: Client):
    logger.error(f"{app.name} | Disconnected from Telegram, exiting")
    sys.exit(1)


ignore_types = (UpdateChannelWebPage, UpdateNewAuthorization, UpdateStory, UpdatePinnedChannelMessages, UpdateChannelMessageViews, UpdateChannelUserTyping)
message_types = (UpdateNewMessage, UpdateEditMessage, UpdateNewChannelMessage, UpdateEditChannelMessage)


async def process_raw(client, update, users, chats, app):
    if isinstance(update, UpdateChannelTooLong):
        logger.warning(f"{app.name} | Channel update too long")
        return

    if isinstance(update, ignore_types):
        return

    if isinstance(update, message_types):
        message = update.message
        if getattr(message, "processed", False):
            return

        has_text = hasattr(message, "text") and message.text.strip()
        if not has_text:
            return

    raw_type = type(update)
    if "delete" in str(raw_type).lower():
        return

    chat_ids = []
    for chat_id, chat in chats.items():
        chat_ids.append(chat_id)

    logger.info(f"{app.name} | Raw handle {raw_type}\n in {chat_ids}")
    for chat_id, chat in chats.items():
        if not isinstance(chat, Channel):
            continue

        if not getattr(chat, "username", None):
            if isinstance(update, UpdateNewMessage) or isinstance(update, UpdateNewChannelMessage):
                message = update.message
                text = getattr(message, "text", None)
                m = getattr(message, "message", None)
                logger.info(f"{app.name} | Message from unknown chat {chat_id} in raw {chat}:\n{message}\n{text}\n{m}")


async def process_message(app, message: Message, edit):
    global rabbitmq_channel, total_messages, total_send_messages
    message.processed = True

    payload = message_to_payload(app, message)

    total_messages += 1
    logger.debug(f"{app.name} | {total_messages} -> {total_send_messages} | Processed {payload['message_id']} from {payload['chat_id']}")

    try:
        queue.put_nowait(payload)
    except asyncio.QueueFull:
        logger.warning(f"{app.name} | Queue is full, dropping message {payload['message_id']} from {payload['chat_id']}")


def message_to_payload(app, message: Message) -> dict:
    return {
        "chat_title": str(message.chat.title) if message.chat.title else None,
        "chat_username": str(message.chat.username) if message.chat.username else None,
        "user_id": str(message.from_user.id) if message.from_user and message.from_user.id else None,
        "user_username": str(message.from_user.username) if message.from_user and message.from_user.username else None,
        "user_firstname": (str(message.from_user.first_name) if message.from_user and message.from_user.first_name else None),
        "user_lastname": (str(message.from_user.last_name) if message.from_user and message.from_user.last_name else None),
        "chat_id": str(message.chat.id),
        "message_id": message.id,
        "text": message.text,
        "created_at": message.date.isoformat(),
        "app": app,
        "reply_markup": message.reply_markup,
    }


async def rabbitmq_job(worker: int):
    global total_send_messages
    logger.info(f"RabbitMQ produce worker {worker} started")
    while True:
        payload = await queue.get()

        app = payload["app"]
        chat_id = payload["chat_id"]
        message_id = str(payload["message_id"])
        await safe_redis_op(redis_client.hset(f"last_id:{app.name}", chat_id, message_id))

        try:
            reply_markup = payload["reply_markup"]
            if reply_markup and hasattr(reply_markup, "inline_keyboard") and len(reply_markup.inline_keyboard) > 0:
                before = payload["user_username"]
                before_id = payload["user_id"]
                handle = await process_buttons(payload)
                if handle is ButtonsHandle.SKIPPED:
                    logger.debug(f"{app.name} | Message skipped due to spam button text")
                    continue
                elif handle is ButtonsHandle.FAILED:
                    raise Exception(f"{app.name} | Failed to process buttons: {payload}")
                elif handle is ButtonsHandle.IGNORED:
                    if any(payload["text"].endswith(text) for text in SPAM_TEXT_ENDS):
                        logger.debug(f"{app.name} | Message {message_id} from {chat_id} skipped due to spam")
                        continue
                    else:
                        logger.info(f"{app.name} | All buttons ignored: {before} -> {payload['user_username']}, {before_id} -> {payload['user_id']}")
                else:
                    logger.info(f"{app.name} | Buttons processed: {before} -> {payload['user_username']}, {before_id} -> {payload['user_id']}")

            payload.pop("app", None)
            payload.pop("reply_markup", None)
            await rabbitmq_channel.default_exchange.publish(routing_key=queue_name, message=aio_pika.Message(body=json.dumps(payload).encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT))
            size = queue.qsize()
            if size % 100 == 0 and size > 0:
                logger.info(f"Queue size: {size}")
            total_send_messages += 1
            logger.trace(f"{app.name} | Sent message {message_id} from {chat_id} to RabbitMQ")
        except Exception as e:
            logger.warning(f"{app.name} | Failed to send message {message_id} from {chat_id} to RabbitMQ: {e}")
        finally:
            queue.task_done()


async def process_buttons(payload):
    app: Client = payload["app"]
    chat_username = payload["chat_username"]
    buttons_rows: list[list[InlineKeyboardButton]] = payload["reply_markup"].inline_keyboard

    handler = select_handler(chat_username)
    return await handle_buttons(buttons_rows, partial(handler, app=app, payload=payload))


def select_handler(chat_username: str):
    handler = EXACT_RULES.get(chat_username)
    if handler:
        return handler

    for prefix, handler in PREFIX_RULES.items():
        if chat_username and chat_username.startswith(prefix):
            return handler

    return DEFAULT_HANDLER


async def check_connected(app):
    while True:
        await asyncio.sleep(1800)
        if app.is_connected:
            try:
                await app.ping()
                logger.info(f"{app.name} | Online ping")
            except Exception as e:
                logger.warning(f"{app.name} | Online ping failed: {e}")
        else:
            logger.info(f"{app.name} | Offline ping")


async def sync_pull(app: Client):
    global total_messages

    delay = random.uniform(10, 120)
    logging.info(f"{app.name} | Pull will initiate in about {int(delay)} seconds.")
    await asyncio.sleep(delay)
    logging.info(f"{app.name} | Pull started.")

    while True:
        processed_chats = 0
        total_pulled_messages = 0
        try:
            state = await app.invoke(GetState())
            await app.invoke(GetDifference(pts=state.pts, date=state.date, qts=state.qts))

            async for dialog in app.get_dialogs():
                pulled_messages = 0
                processed_chats += 1
                if not dialog.chat or not dialog.top_message:
                    continue

                chat_id = dialog.chat.id
                top_id = dialog.top_message.id
                redis_key = f"last_id:{app.name}"

                res = await safe_redis_op(redis_client.hget(redis_key, str(chat_id)))

                if res is None:
                    logging.info(f"{app.name} | New chat {chat_id} history. Pulling last {PULL_LIMIT} messages.")
                    async for message in app.get_chat_history(chat_id, limit=PULL_LIMIT):
                        if message.text:
                            await queue.put(message_to_payload(app, message))
                            total_messages += 1
                            pulled_messages += 1
                            total_pulled_messages += 1
                    await safe_redis_op(redis_client.hset(redis_key, str(chat_id), str(top_id)))
                    delay = PULL_INTERVAL + random.uniform(-30, 30)
                    logging.info(f"{app.name} | Pull for {processed_chats} chat processed {pulled_messages} messages, next chat delayed for about {int(delay)} seconds.")
                    await asyncio.sleep(delay)
                    continue

                last_id = int(res)
                gap_size = top_id - last_id

                if gap_size > 0:
                    if gap_size > GAP_WARNING_THRESHOLD:
                        logging.warning(f"{app.name} | Pull chat {processed_chats} ({chat_id}) is critical missing for {gap_size}!")

                    limit = min(gap_size, PULL_LIMIT)
                    max_seen_id = last_id
                    async for message in app.get_chat_history(chat_id, limit=limit):
                        if message.id > last_id:
                            max_seen_id = max(max_seen_id, message.id)
                            if message.text:
                                await queue.put(message_to_payload(app, message))
                                total_messages += 1
                                pulled_messages += 1
                                total_pulled_messages += 1

                    if max_seen_id > last_id:
                        await safe_redis_op(redis_client.hset(redis_key, str(chat_id), str(max_seen_id)))

                    delay = PULL_INTERVAL + random.uniform(-30, 30)
                    logging.info(f"{app.name} | Pull for {processed_chats} chat processed {pulled_messages} messages, next chat delayed for about {int(delay)} seconds.")
                    await asyncio.sleep(delay)
            delay = PULL_INTERVAL + random.uniform(-30, 30)
            logging.info(f"{app.name} | Pull ended for {processed_chats} chats and processed {total_pulled_messages} messages, next pull delayed for about {int(delay)} seconds.")
            await asyncio.sleep(delay)
        except errors.FloodWait as e:
            delay = e.value + 10
            logging.warning(f"{app.name} | FloodWait: {e.value}, waiting {delay} seconds.")
            await asyncio.sleep(delay)
        except Exception as e:
            logging.error(f"{app.name} | Pull failed: {e}")
            await asyncio.sleep(30)


async def safe_redis_op(operation):
    try:
        return await operation
    except Exception as e:
        logging.error(f"Redis Error: {e}")
    return None


async def init_redis():
    global redis_client

    validate_env("REDIS_PASSWORD")

    # fmt: off
    redis_client = redis.Redis(
        host=os.environ.get("REDIS_HOST", "redis"),
        port=int(os.environ.get("REDIS_PORT", 6379)),
        password=os.environ["REDIS_PASSWORD"],
        db=0, max_connections=20, decode_responses=True
    )
    # fmt: on


async def init_rabbitmq():
    global rabbitmq_channel, rabbitmq_connection

    host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
    port = os.environ.get("RABBITMQ_PORT", 5672)
    vhost = os.environ.get("RABBITMQ_VHOST", "/")
    user = os.environ.get("RABBITMQ_USER", "cardinal")
    password = os.environ["RABBITMQ_PASS"]
    if not password:
        raise ValueError("Переменная окружения 'RABBITMQ_PASS' не установлена или пуста!")

    rabbitmq_connection = await aio_pika.connect_robust(f"amqp://{user}:{password}@{host}:{port}{vhost}")
    rabbitmq_channel = await rabbitmq_connection.channel()
    await rabbitmq_channel.declare_queue(queue_name, durable=True)


async def run_worker(worker_id: int):
    while True:
        try:
            await rabbitmq_job(worker_id)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning(f"RabbitMQ produce worker {worker_id} will restart in 5 seconds, crashed due: {e}.")
            await asyncio.sleep(5)


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    logger.info("Bot startup initiated.")

    worker_tasks = []

    try:
        await init_rabbitmq()
        logger.info(f"Connected to RabbitMQ.")
        for i in range(rabbitmq_workers):
            worker_tasks.append(asyncio.create_task(run_worker(i)))
    except Exception as e:
        logger.info(f"Failed to connect to RabbitMQ: {e}")
        return

    try:
        await init_redis()
        logger.info(f"Connected to Redis.")
    except Exception as e:
        logger.info(f"Failed to connect to Redis: {e}")
        return

    api_id = os.environ["TELEGRAM_API_ID"]
    if not api_id:
        raise ValueError("Переменная окружения 'TELEGRAM_API_ID' не установлена или пуста!")

    api_hash = os.environ["TELEGRAM_API_HASH"]
    if not api_hash:
        raise ValueError("Переменная окружения 'TELEGRAM_API_HASH' не установлена или пуста!")

    pyro_sessions = os.environ.get("PYRO_SESSIONS", "cardinal")
    pyro_sessions = [s.strip() for s in pyro_sessions.split(",") if s.strip()]

    for i, pyro_session in enumerate(pyro_sessions):
        app = Client(
            name=pyro_session,
            api_id=api_id,
            api_hash=api_hash,
            workers=pyrogram_workers,
            skip_updates=False,
            max_business_user_connection_cache_size=10,
            max_message_cache_size=500,
            workdir="/app/pyrogram-sessions",
        )
        app.add_handler(MessageHandler(partial(process_message, edit=False), filters.text & ~filters.me), group=0)
        app.add_handler(EditedMessageHandler(partial(process_message, edit=True), filters.text & ~filters.me), group=1)
        app.add_handler(RawUpdateHandler(partial(process_raw, app=app)), group=2)
        apps[i] = app
        logger.info(f"{app.name} | Message listener assigned.")

    try:
        dialogs = set()
        apps_list = list(apps.items())
        for index, (key, app) in enumerate(apps_list):
            try:
                logger.info(f"{app.name} | Startup initiated.")
                await app.start()
                app.add_handler(DisconnectHandler(callback=disconnect))
                logger.info(f"{app.name} | Disconnect handler assigned.")

                asyncio.create_task(check_connected(app))
                if os.getenv("CHECK_DUPLICATES", "false") == "true":
                    await check_duplicates(app, dialogs)
                if os.getenv("ENABLE_PULL", "true") == "true":
                    asyncio.create_task(sync_pull(app))

                if index == len(apps_list) - 1:
                    logger.info(f"{app.name} | Startup finished.")
                else:
                    delay = random.uniform(30, 120)
                    logger.info(f"{app.name} | Startup finished. Next app delayed for about {int(delay)} seconds.")
                    await asyncio.sleep(delay)
            except Exception as e:
                logger.warning(f"{app.name} | Failed to start: {e}")
                apps.pop(key)
        if len(apps) == 0:
            logger.error(f"Bot failed to start: {len(apps)} app initiated")
            sys.exit(1)
        else:
            logger.info(f"Bot started. Total {len(apps)} apps.")
        await asyncio.sleep(1)
        await idle()
    except Exception as e:
        logger.error(f"[!] Unexpected exception: {e}")
    finally:
        for task in worker_tasks:
            task.cancel()
        await asyncio.gather(*worker_tasks, return_exceptions=True)
        for i, app in apps.items():
            if app.is_connected:
                await app.stop()
                logger.info(f"{app.name} | Stopped.")
        logger.info("Bot stopped.")
        await rabbitmq_connection.close()
        logger.info("RabbitMQ connection closed.")


async def check_duplicates(app: Client, dialogs: set[Any]):
    named = 0
    non_named = 0

    async for dialog in app.get_dialogs():
        if dialog.chat.id in dialogs:
            logger.warning(f"{app.name} | Duplicate dialog {dialog.chat.id} {dialog.chat.title} {dialog.chat.type} {dialog.chat.username}")
        else:
            dialogs.add(dialog.chat.id)
        if dialog.chat.username is None:
            non_named += 1
        else:
            named += 1
    logger.info(f"{app.name} | Total {named} named dialogs and {non_named} non-named dialogs")


if __name__ == "__main__":
    asyncio.run(main())
