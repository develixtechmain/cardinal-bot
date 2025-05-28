import asyncio
import json
import os

import aio_pika
import clickhouse_driver
import httpx
from aio_pika.abc import AbstractRobustChannel, AbstractRobustQueue
from clickhouse_driver import Client
from dateutil.parser import isoparse
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import SystemMessagePromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from pydantic import SecretStr

load_dotenv()

rabbitmq_connection: aio_pika.RobustConnection
rabbitmq_channel: AbstractRobustChannel
rabbitmq_queue: AbstractRobustQueue
queue_name = "tg_queue"

llm: ChatOpenAI
click: clickhouse_driver.Client


async def process_message(body: bytes, message: aio_pika.abc.AbstractIncomingMessage):
    async with message.process():
        try:
            message = json.loads(body)
        except Exception as e:
            print(f"Invalid JSON format: {e}")
            return

        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": os.environ["EMBEDDER_KEY"],
        }
        async with httpx.AsyncClient() as client:
            resp_data = {"is_found": True, "embedded": []}
            # try:
            #     resp = await client.post(os.environ["EMBEDDER_URL"], json={"message":message["text"]}, headers=headers)
                # resp.raise_for_status()
                # resp_data = resp.json()
            # except Exception as e:
            #     print(f"Failed to process request to foo: {e}")
            #     raise

        is_found = resp_data.get("is_found", False)
        if not isinstance(is_found, bool):
            print("Unexpected response: is_found not bool")
            raise ValueError("Expected 'is_found' to be a boolean")

        if not is_found:
            return

        text = message['text']
        system_prompt = SystemMessagePromptTemplate.from_template((
            "You must respond strictly with plaintext only: `true` or `false`. "
            "Evaluate whether the input message is a job offer or lead. This includes: "
            "— Messages offering employment, freelance work, collaboration, gigs, or any form of professional opportunity. "
            "— Messages expressing interest in services, collaboration, or potential business engagement. "
            "Do not explain your answer. Do not include any additional words, characters, or formatting. "
            "Respond with exactly `true` or `false`."
        )).format()

        messages = [
            system_prompt,
            HumanMessage(content=text)
        ]

        try:
            result = (await llm.ainvoke(messages)).content
        except Exception as e:
            print(f"Failed to process message {message['message_id']} from {message['chat_id']} via llm: {e}")
            result = "false"

        print(f"LLM result: {result}")

        if result.strip().lower() == "true":
            chat_id = str(message['chat_id'])
            chat_title = str(message['chat_title'])
            chat_username = str(message['chat_username'])

            user_id = str(message['user_id'])
            user_username = str(message['user_username'])
            user_firstname = str(message['user_firstname'])
            user_lastname = str(message['user_lastname'])

            message_id = message['message_id']
            created_at = isoparse(message['created_at'])

            click_data = [
                [
                    chat_id, chat_title, chat_username,
                    user_id, user_username, user_firstname, user_lastname,
                    int(message_id), str(text), resp_data['embedded'], created_at
                ]
            ]

            try:
                click.execute("""
                    INSERT INTO telegram_messages 
                    (chat_id, chat_title, chat_username, 
                    user_id, user_username, user_firstname, user_lastname, 
                    message_id, text, text_vector, created_at)
                    VALUES
                """, click_data)
                print(f"Message {message_id} from {chat_id} saved to ClickHouse")
            except Exception as e:
                print(f"Failed to save message {message_id} from {chat_id} to ClickHouse: {e}")


async def init_rabbitmq():
    global rabbitmq_channel, rabbitmq_connection, rabbitmq_queue

    host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
    port = os.environ.get("RABBITMQ_PORT", 5672)
    vhost = os.environ.get("RABBITMQ_VHOST", "/")
    user = os.environ.get("RABBITMQ_USER", "cardinal")
    password = os.environ["RABBITMQ_PASS"]
    if not password:
        raise ValueError("Переменная окружения 'RABBITMQ_PASS' не установлена или пуста!")

    rabbitmq_connection = await aio_pika.connect_robust(f"amqp://{user}:{password}@{host}:{port}{vhost}")
    rabbitmq_channel = await rabbitmq_connection.channel()
    rabbitmq_queue = await rabbitmq_channel.declare_queue(queue_name, durable=True)


async def init_click():
    global click
    password = os.environ["CLICKHOUSE_PASS"]
    if not password:
        raise ValueError("Переменная окружения 'CLICKHOUSE_PASS' не установлена или пуста!")
    click = Client(
        host=os.environ.get("CLICKHOUSE_HOST", "clickhouse"),
        database=os.environ.get("CLICKHOUSE_DATABASE", "cardinal"),
        user=os.environ.get("CLICKHOUSE_USER", "cardinal"),
        password=password,
    )
    click.execute("""
    CREATE TABLE IF NOT EXISTS telegram_messages (
        chat_id String,
        chat_title String,
        chat_username String,
        user_id String,
        user_username String,
        user_firstname String,
        user_lastname String,
        message_id UInt64,
        text String,
        text_vector Array(Float32),
        created_at DateTime
    ) ENGINE = MergeTree()
    ORDER BY (chat_id, message_id)
    """)


async def init_llm():
    global llm

    ai_key = os.environ["OPENAI_API_KEY"]
    if not ai_key:
        raise ValueError("Переменная окружения 'CLICKHOUSE_PASSWORD' не установлена или пуста!")

    llm = ChatOpenAI(
        api_key=SecretStr(ai_key)
    )

def validate_env(env):
    if not os.environ[env]:
        raise ValueError(f"Переменная окружения '{env}' не установлена или пуста!")

async def main():
    global rabbitmq_queue

    print("Listener startup initiated.")

    try:
        await init_rabbitmq()
        print(f"Connected to RabbitMQ.")
    except Exception as e:
        print(f"Failed to connect to RabbitMQ: {e}")
        return

    try:
        await init_click()
        print(f"Connected to ClickHouse.")
    except Exception as e:
        print(f"Failed to connect to ClickHouse: {e}")
        return

    try:
        await init_llm()
        print(f"LLM initiated.")
    except Exception as e:
        print(f"Failed init LLM : {e}")
        return

    try:
        for env in ["EMBEDDER_URL", "EMBEDDER_KEY"]:
            validate_env(env)
    except Exception as e:
        print(f"Failed to init llm: {e}")
        return

    print(f"Listener started.")

    try:
        async with rabbitmq_queue.iterator() as queue_iter:
            async for message in queue_iter:
                asyncio.create_task(process_message(message.body, message))
    finally:
        await click.disconnect()
        print("ClickHouse connection closed.")
        await rabbitmq_connection.close()
        print("RabbitMQ connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
