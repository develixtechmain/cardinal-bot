# ai_core

## Назначение

AI-сервис для онбординга кандидатов и управления правилами фильтрации. Использует LLM (OpenAI GPT-4.1-mini) через LangChain для анализа анкет, извлечения навыков и валидации заявок.

## Технологии

- Python 3.11, FastAPI, Uvicorn (порт 8000)
- LangChain + OpenAI (GPT-4.1-mini)
- AsyncPG (PostgreSQL)
- PyJWT (аутентификация)
- Docker (python:3.11-slim)

## Структура файлов

| Файл | Назначение |
|---|---|
| `main.py` | Точка входа: FastAPI-приложение, роуты, middleware |
| `ai.py` | LLM-логика: анализ ответов, облако смыслов, вывод должности, проверка/извлечение правил |
| `db.py` | Слой данных: PostgreSQL-пул, LRU-кеш пользователей и онбордингов |
| `security.py` | JWT + API Key аутентификация |
| `utils.py` | Валидация переменных окружения |
| `Dockerfile` | Контейнеризация |

## API-эндпоинты

| Метод | Путь | Auth | Описание |
|---|---|---|---|
| POST | `/api/onboarding/start` | JWT | Создать онбординг |
| POST | `/api/onboarding/{id}/answer` | JWT | Отправить ответы на вопросы |
| POST | `/api/onboarding/{id}/complete` | JWT | Завершить онбординг → получить title + tags |
| POST | `/api/rules/check` | API Key | Проверить текст по правилам фильтрации |
| POST | `/api/rules/extract` | API Key | Извлечь правила из обратной связи |

## AI-функции (ai.py)

- **process_answer()** — проверяет полноту анкеты (≥50 значимых фраз), генерирует дополнительные вопросы
- **get_cloud_of_meaning()** — извлекает облако навыков/тегов из анкеты
- **get_task_title()** — определяет должность по набору тегов
- **check_rules()** — валидирует заявку по правилам формата "IF ... THEN DO NOT RECOMMEND"
- **extract_rules()** — генерирует новые правила из пользовательского фидбека

## Аутентификация

- **JWT** (HS256) — для `/api/onboarding/*` эндпоинтов
- **API Key** (заголовок `X-API-KEY`) — для `/api/rules/*` эндпоинтов

## Подключения

- **Входящие**: backend, фронтенд (через JWT)
- **Исходящие**: OpenAI API, PostgreSQL

## Переменные окружения

| Переменная | Обязательная | Описание |
|---|---|---|
| `OPENAI_API_KEY` | Да | Ключ OpenAI |
| `SECURITY_KEY` | Да | JWT-секрет |
| `API_KEY` | Да | Ключ для /api/rules |
| `DB_PASS` | Да | Пароль PostgreSQL |
| `AI_MODE` | Да | "prod" / "debug" |
| `DB_HOST` | Нет | По умолчанию "postgresql" |
| `DB_PORT` | Нет | По умолчанию 5432 |
