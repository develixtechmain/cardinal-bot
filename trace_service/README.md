# Message trace service

Отдельный сервис для записи и просмотра цепочки обработки сообщений (correlation id, события в PostgreSQL, REST API и статический UI).

## Запуск локально

```bash
cd trace_service
pip install -r requirements.txt
export TRACE_SERVICE_API_KEY=your-secret
export DB_HOST=localhost DB_PORT=5432 DB_USER=... DB_PASS=... DB_NAME=cardinal
uvicorn main:app --host 0.0.0.0 --port 8010
```

- Документация API: `http://localhost:8010/docs`
- UI: `http://localhost:8010/` или `http://localhost:8010/ui/`

При старте выполняется `schema.sql` (создание таблиц при отсутствии).

## Эмиттеры (другие сервисы)

Переменные:

- `TRACE_SERVICE_URL` — базовый URL (например `http://trace-service:8010`)
- `TRACE_INGEST_KEY` — тот же секрет, что и `TRACE_SERVICE_API_KEY` на сервисе

POST ` /internal/traces/events` с заголовком `X-Trace-API-Key`.

## Тесты

```bash
cd trace_service
TRACE_SERVICE_SKIP_DB_INIT=1 python3 -m pytest -q
```

`TRACE_SERVICE_SKIP_DB_INIT=1` отключает подключение к БД при импорте (для тестов с мок-пулом).
