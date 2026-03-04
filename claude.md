# Cardinal

## Описание проекта

Cardinal — платформа для AI-поиска лидов и рекомендаций на базе Telegram. Система парсит сообщения из Telegram-каналов/чатов, анализирует их с помощью LLM, находит релевантных кандидатов через векторный поиск и доставляет рекомендации пользователям.

## Архитектура

Микросервисная архитектура с асинхронной обработкой через RabbitMQ.

### Поток данных

```
Telegram → telegram_parser → RabbitMQ → message_processor → [AI Core + Embeddings]
                                              ↓
                                         PostgreSQL
                                         ClickHouse
                                         Qdrant (векторная БД)
                                              ↓
                                    backend → Telegram Bot → Пользователь
```

## Модули

| Директория | Технологии | Назначение |
|---|---|---|
| [`app/`](app/claude.md) | React 19, TypeScript, Vite, Zustand | Telegram Mini App — фронтенд |
| [`backend/`](backend/claude.md) | Python, FastAPI, Aiogram | Основной API, Telegram-боты, платежи, подписки |
| [`ai_core/`](ai_core/claude.md) | Python, FastAPI, LangChain, OpenAI | AI-сервис: онбординг, извлечение правил |
| [`message_processor/`](message_processor/claude.md) | Python, LangChain, OpenAI | Обработчик сообщений из очереди RabbitMQ |
| [`embedding_processor/`](embedding_processor/claude.md) | C#, ASP.NET Core 9, EF Core | Управление векторными эмбеддингами, семантический поиск |
| [`telegram_parser/`](telegram_parser/claude.md) | Python, Pyrogram | Сбор сообщений из Telegram в RabbitMQ |

## Технологический стек

- **Фронтенд**: React 19, TypeScript, Vite, Zustand, Wouter, Telegram Web App SDK
- **Бэкенд**: Python 3.11, FastAPI, Aiogram
- **AI/ML**: LangChain, OpenAI GPT-4, Hugging Face (intfloat/multilingual-e5-base)
- **Базы данных**: PostgreSQL, ClickHouse, Redis, Qdrant
- **Очереди**: RabbitMQ (aio-pika)
- **Инфраструктура**: Docker Compose, приватный Docker-реестр
- **Мониторинг**: Prometheus, Loki, LangSmith

## Инфраструктура

- **Развёртывание**: Docker Compose (`docker-compose.yml` — dev, `deploy.yml` — prod)
- **Реестр**: `162.120.16.215:54710` (приватный Docker registry)
- **Домен**: `cardinal-x.online`
- **Версия**: `0.0.3-SNAPSHOT`

## Ключевые сервисы (Docker)

| Сервис | Порт | RAM |
|---|---|---|
| app | 3000 | — |
| backend-core | 8000 | 512MB |
| ai-core | 8088 | 512MB |
| message-processor | — | 512MB |
| embeddings-processor | — | 512MB |
| telegram-parser | — | 256MB |
| qdrant | 6333 | 512MB |
| rabbitmq | 5672 | 512MB |
| redis | 6379 | — |
| postgresql | 5432 | 512MB |
| embeddings (HF) | — | 6GB |

## Общие переменные окружения

- `SECURITY_KEY` — JWT-секрет
- `BOT_TOKEN`, `RECOMMENDATION_BOT_TOKEN` — Telegram-боты
- `OPENAI_API_KEY` — ключ OpenAI
- `RABBITMQ_PASS`, `DB_PASS`, `REDIS_PASSWORD` — пароли БД
- `QDRANT_KEY` — ключ Qdrant
- `LAVA_KEY`, `ALPHA_KEY` — платёжные шлюзы
- `LANGSMITH_API_KEY` — трейсинг AI
