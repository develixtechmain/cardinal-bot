# telegram_parser

## Назначение

Сервис-слушатель Telegram-сообщений. Подключается к Telegram через Pyrogram, слушает текстовые сообщения из чатов/каналов и публикует их в очередь RabbitMQ для дальнейшей обработки.

Это **входная точка** конвейера данных Cardinal.

## Технологии

- Python 3.11
- Pyrogram (pyrofork) — Telegram-клиент
- aio-pika — асинхронный RabbitMQ-клиент
- tgcrypto — шифрование Telegram
- Docker (python:3.11-slim)

## Структура файлов

| Файл | Назначение |
|---|---|
| `main.py` | Единственный исходный файл: инициализация Pyrogram и RabbitMQ, обработчик сообщений |
| `requirements.txt` | Зависимости (4 пакета) |
| `Dockerfile` | Контейнеризация |

## Логика работы (main.py)

1. **init_rabbitmq()** — подключение к RabbitMQ, создание durable-очереди `tg_queue`
2. **process_message()** — обработчик каждого входящего сообщения:
   - Извлекает метаданные: chat_id, chat_title, user_id, user_username и т.д.
   - Сериализует в JSON
   - Публикует в очередь `tg_queue` с persistent delivery mode
3. **main()** — инициализация Pyrogram-клиента, регистрация обработчика для текстовых сообщений

## Формат сообщения в очереди

```json
{
  "chat_id": "string",
  "chat_title": "string",
  "chat_username": "string",
  "user_id": "string",
  "user_username": "string",
  "user_firstname": "string",
  "user_lastname": "string",
  "message_id": "integer",
  "text": "string",
  "created_at": "ISO-8601"
}
```

## Подключения

- **Входящие**: Telegram API (Pyrogram)
- **Исходящие**: RabbitMQ (очередь `tg_queue`)

## Переменные окружения

| Переменная | Обязательная | Описание |
|---|---|---|
| `TELEGRAM_API_ID` | Да | ID приложения Telegram |
| `TELEGRAM_API_HASH` | Да | Hash приложения Telegram |
| `RABBITMQ_PASS` | Да | Пароль RabbitMQ |
| `RABBITMQ_HOST` | Нет | По умолчанию "rabbitmq" |
| `RABBITMQ_PORT` | Нет | По умолчанию 5672 |
| `RABBITMQ_USER` | Нет | По умолчанию "cardinal" |
| `PYRO_SESSION` | Нет | Имя сессии Pyrogram |
