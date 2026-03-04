# backend

## Назначение

Основной бэкенд-сервис Cardinal. REST API + Telegram-боты для управления пользователями, задачами поиска лидов, подписками, платежами и реферальной системой.

## Технологии

- Python 3.11, FastAPI, Uvicorn (порт 8000)
- Aiogram — Telegram-боты
- AsyncPG — PostgreSQL
- httpx — HTTP-клиент для внешних сервисов
- PyJWT — аутентификация
- Prometheus — метрики
- Docker (python:3.11-slim)

## Структура

| Директория | Назначение |
|---|---|
| [`api/`](api/claude.md) | REST API роутеры (auth, users, finder, subscriptions, refs) |
| [`bot/`](bot/claude.md) | Telegram-боты (основной + рекомендации) |
| [`service/`](service/claude.md) | Слой данных: БД, бизнес-логика, кеширование |

### Файлы корневого уровня

| Файл | Назначение |
|---|---|
| `main.py` | Точка входа FastAPI: lifespan, middleware (JWT/Webhook/API Key), CORS, метрики |
| `ai.py` | Клиент AI Core: check_rules(), extract_rules() |
| `embedding.py` | Клиент Embedding Processor: save_tags(), accept/decline_recommendation() |
| `lava.py` | Клиент платёжного шлюза Lava.top: создание инвойсов, статусы, отмена подписок |
| `alpha.py` | Клиент Alfa Bank: создание заказов, статусы платежей |
| `consts.py` | Перечисления (TransactionStatus, SubscriptionPeriod) и тарифы |
| `utils.py` | Валидация env-переменных |

## Трёхуровневая аутентификация

1. **Webhook Auth** — секретный токен для `/api/webhook` и `/api/finder/recommendations/webhook`
2. **API Key** (`X-API-KEY`) — для `/api/finder/recommendations/send` и `/api/subscriptions/webhook/lava`
3. **JWT** (Bearer) — для всех остальных защищённых эндпоинтов (30 мин access, 7 дней refresh)

## Тарифы

| Период | Цена (₽) |
|---|---|
| 1 месяц | 4 900 |
| 3 месяца | 12 500 |
| 12 месяцев | 42 000 |

## Подключения

| Сервис | Направление | Назначение |
|---|---|---|
| PostgreSQL | IN/OUT | Основная БД |
| AI Core | OUT | Проверка/извлечение правил |
| Embedding Processor | OUT | Сохранение тегов, feedback |
| Lava.top | OUT | Платёжный шлюз |
| Alfa Bank | OUT | Платёжный шлюз |
| Telegram API | IN/OUT | Вебхуки ботов |

## Переменные окружения

| Переменная | Обязательная | Описание |
|---|---|---|
| `SECURITY_KEY` | Да | JWT-секрет |
| `BOT_TOKEN` | Да | Основной Telegram-бот |
| `RECOMMENDATION_BOT_TOKEN` | Да | Бот рекомендаций |
| `API_KEY` | Да | Внутренний API-ключ |
| `WEBHOOK_KEY` | Да | Секрет Telegram-вебхуков |
| `WEBHOOK_URL` | Да | URL бэкенда для вебхуков |
| `DB_PASS` | Да | Пароль PostgreSQL |
| `LAVA_KEY` | Да | Ключ Lava.top |
| `ALPHA_KEY` | Да | Ключ Alfa Bank |
| `AI_CORE_KEY`, `AI_CORE_HOST` | Да | AI Core сервис |
| `EMBEDDINGS_PROCESSOR_KEY`, `EMBEDDINGS_PROCESSOR_HOST` | Да | Embedding Processor |
| `ENABLE_METRICS` | Нет | Включить Prometheus |
