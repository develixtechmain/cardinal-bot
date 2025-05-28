import asyncio
import json
import os

import aio_pika
from aio_pika.abc import AbstractRobustChannel
from dotenv import load_dotenv
from pyrogram import Client, filters, idle
from pyrogram.handlers import MessageHandler

load_dotenv()

rabbitmq_connection: aio_pika.RobustConnection
rabbitmq_channel: AbstractRobustChannel
queue_name = "tg_queue"


# @app.on_message(filters.text & ~filters.me)
async def process_message(_, message):
    global rabbitmq_channel

    payload = {
        "chat_id": str(message.chat.id),
        "chat_title": str(message.chat.title) if message.chat.title else "private",
        "chat_username": str(message.chat.username) if message.chat.username else "none",
        "user_id": str(message.from_user.id) if message.from_user else "unknown",
        "user_username": str(message.from_user.username) if message.from_user else "unknown",
        "user_firstname": str(message.from_user.first_name) if message.from_user else "unknown",
        "user_lastname": str(message.from_user.last_name) if message.from_user else "unknown",
        "message_id": message.id,
        "text": message.text,
        "created_at": message.date.isoformat(),
    }

    try:
        await rabbitmq_channel.default_exchange.publish(
            routing_key=queue_name,
            message=aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ))
        print(f"[>] Sent message {message.id} from {message.chat.id} to RabbitMQ")
    except Exception as e:
        print(f"[!] Failed to send message {message.id} from {message.chat.id} to RabbitMQ: {e}")


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


async def main():
    print("Bot startup initiated.")

    try:
        await init_rabbitmq()
        print(f"Connected to RabbitMQ.")
    except Exception as e:
        print(f"Failed to connect to RabbitMQ: {e}")
        return

    session = os.environ.get("PYRO_SESSION", "session")
    api_id = os.environ["TELEGRAM_API_ID"]
    if not api_id:
        raise ValueError("Переменная окружения 'TELEGRAM_API_ID' не установлена или пуста!")

    api_hash = os.environ["TELEGRAM_API_HASH"]
    if not api_hash:
        raise ValueError("Переменная окружения 'TELEGRAM_API_HASH' не установлена или пуста!")

    app = Client(
        name=session,
        api_id=api_id,
        api_hash=api_hash,
    )

    app.add_handler(MessageHandler(process_message, filters.text & ~filters.me))
    print("Message listener assigned.")

    try:
        await app.start()
        print("Bot started.")
        await idle()
    finally:
        await app.stop()
        print("Bot stopped.")
        await rabbitmq_connection.close()
        print("RabbitMQ connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
