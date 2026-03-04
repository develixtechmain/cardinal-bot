# message_processor

## Назначение

Асинхронный обработчик сообщений из RabbitMQ. Принимает сообщения из Telegram, классифицирует их через LLM как потенциальные лиды, ищет релевантных кандидатов через векторный поиск и доставляет рекомендации пользователям.

Это **ядро рекомендательной системы** Cardinal.

## Технологии

- Python 3.11, asyncio
- aio-pika — RabbitMQ-потребитель (очередь `tg_queue`)
- LangChain + OpenAI (gpt-4-mini) — классификация лидов
- httpx — HTTP-клиент для внешних сервисов
- asyncpg — PostgreSQL
- clickhouse-driver — ClickHouse (аналитика)
- Docker (python:3.11-slim)

## Структура файлов

| Файл | Назначение |
|---|---|
| `main.py` | Основная логика: обработка сообщений, рейтинг кандидатов, сохранение рекомендаций |
| `ai.py` | Классификация лидов через LLM (бинарный: лид / не лид) |
| `db.py` | PostgreSQL + ClickHouse: хранение рекомендаций, статистика пользователей, архив сообщений |
| `embedding.py` | Клиент к Embedding Processor: поиск кандидатов, подтверждение рекомендаций |
| `core.py` | Клиент к Backend Core: отправка рекомендаций пользователям |
| `utils.py` | Валидация env-переменных |
| `Dockerfile` | Контейнеризация |

## Конвейер обработки

```
RabbitMQ (tg_queue)
    ↓
Парсинг JSON-сообщения
    ↓
Поиск кандидатов через Embedding Processor
    ↓
Проверка через LLM: это лид?
    ↓
Архивация в ClickHouse
    ↓
Расчёт рейтинга кандидатов
    ↓
Сохранение рекомендации в PostgreSQL
    ↓
Отправка через Backend Core → Telegram Bot → Пользователь
```

## Алгоритм рейтинга кандидатов

Многофакторная формула (main.py → `calculate_rating()`):
- **30%** — Новизна: `1 / (recent_recommendations + 1)`
- **30%** — Score эмбеддинга (семантическое совпадение)
- **25%** — Временной спад: `1 - hours_since_last/3600`
- **15%** — Лояльность: `min(0.1, total_recommendations / 10000)`

Все кандидаты с рейтингом > 90% от лучшего получают рекомендацию. Лимит: **33 рекомендации/день** на пользователя.

## Подключения

| Сервис | Направление | Протокол | Назначение |
|---|---|---|---|
| RabbitMQ | IN | AMQP | Приём сообщений из Telegram |
| PostgreSQL | IN/OUT | asyncpg | Рекомендации, статистика |
| ClickHouse | OUT | clickhouse-driver | Архив метаданных сообщений |
| OpenAI API | OUT | HTTP (LangChain) | Классификация лидов |
| Embedding Processor | IN/OUT | HTTP | Поиск кандидатов |
| Backend Core | OUT | HTTP | Отправка рекомендаций |

## Переменные окружения

| Переменная | Обязательная | Описание |
|---|---|---|
| `RABBITMQ_PASS` | Да | Пароль RabbitMQ |
| `DB_PASS` | Да | Пароль PostgreSQL |
| `CLICKHOUSE_PASS` | Да | Пароль ClickHouse |
| `OPENAI_API_KEY` | Да | Ключ OpenAI |
| `CORE_KEY`, `CORE_HOST` | Да | Backend Core API |
| `EMBEDDINGS_PROCESSOR_KEY`, `EMBEDDINGS_PROCESSOR_HOST` | Да | Embedding Processor API |
