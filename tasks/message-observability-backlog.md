# Бэклог: прозрачность сообщений

Статусы: `[ ]` не начато, `[x]` выполнено.

---

## Фаза 0 — Решения и контракты

- [ ] Утвердить формат `correlation_id` (UUID v4 vs UUID v7/ULID).
- [ ] Утвердить политику для **групповых/частичных** сообщений: один `correlation_id` vs `parent_correlation_id`.
- [ ] Утвердить **retention** событий в PostgreSQL (дни) и нужна ли архивация.
- [ ] Утвердить модель **маскирования** текста в `detail` и кто видит полный контент.
- [ ] Выбрать стратегию записи событий: синхронно в горячем пути vs **async** (очередь/фон).
- [ ] Выбрать размещение **Trace API**: новый сервис vs маршруты в `backend` под `/internal/...`.

---

## Фаза 1 — Схема БД и модуль событий

- [ ] Спроектировать финальную схему таблиц (`message_trace_events`, опционально `message_trace_roots`).
- [ ] Добавить миграции PostgreSQL (Alembic или принятый в проекте инструмент).
- [ ] Реализовать модуль **event writer**: `emit_event(...)`, типы `service`, `stage`, `status`.
- [ ] Добавить индексы: `correlation_id`, `(source_chat_id, source_message_id)`, `occurred_at`.
- [ ] Покрыть writer unit-тестами (мок БД или тестовый контейнер).
- [ ] Добавить метрики Prometheus: `trace_events_written_total`, `trace_events_write_errors_total` (или аналог).

---

## Фаза 2 — Корреляция в telegram_parser

- [ ] Генерировать `correlation_id` при формировании payload для RabbitMQ (первичное появление сообщения).
- [ ] Прокидывать `correlation_id` в JSON тела сообщения в `tg_queue`.
- [ ] (Опционально) Дублировать `correlation_id` в AMQP headers для совместимости с OTel.
- [ ] Эмитить события: `publish` / `queued_internal` с `source_chat_id`, `source_message_id` в `detail` (без лишнего текста).
- [ ] Обновить документацию env/deploy при появлении новых переменных (если есть).

---

## Фаза 3 — Корреляция и события в message_processor

- [ ] Читать `correlation_id` из входящего JSON; для старых сообщений без id — генерировать и логировать `legacy_missing_correlation`.
- [ ] При публикации **частей** через handlers сохранять согласованность id (по решению фазы 0).
- [ ] Эмитить события: `consume`, `redis_dedup_hit` / `redis_dedup_miss`, `handler_short_circuit`, `embedding_search` (результат: found/not_found), `llm_relevance` (агрегированно или по кандидату), `lead_check`, `db_save_message`, `http_recommendation_send` (success/fail).
- [ ] Пробрасывать `X-Correlation-ID` (или согласованный заголовок) в HTTP-клиент к `backend` (`core.send_recommendation_to_user`).
- [ ] Убедиться, что `occurred_at` задаётся в коде шага, а не только время INSERT.

---

## Фаза 4 — Backend: приём и цепочка уведомлений

- [ ] На эндпоинте приёма рекомендаций извлекать correlation из заголовка или тела (согласовать контракт).
- [ ] Эмитить события: `recommendation_received`, `notification_enqueued`, `telegram_send_attempt` / `telegram_send_ok` / `telegram_send_error`.
- [ ] Связать при необходимости `recommendation_id` с корнем трейса (обновление `message_trace_roots` или событие с id).
- [ ] Защитить будущие internal-маршруты от доступа пользовательского JWT без роли (если API совмещён с публичным backend).

---

## Фаза 5 — Trace API

- [ ] Реализовать `GET /internal/traces` с поиском по `correlation_id`, `recommendation_id`, составному `chat_id:message_id`, пагинацией.
- [ ] Реализовать `GET /internal/traces/{correlation_id}` с полным списком событий и сортировкой по времени.
- [ ] Реализовать `GET /internal/traces/{correlation_id}/summary` (краткая сводка для списка).
- [ ] Включить аутентификацию internal-only (API key, отдельный middleware).
- [ ] OpenAPI / схемы ответов для фронта.
- [ ] Интеграционные тесты API (test client + БД).

---

## Фаза 6 — Internal UI

- [ ] Создать проект SPA (или модуль) и базовый layout (поиск + навигация).
- [ ] Экран **поиска**: поле ввода, фильтры по дате/статусу, таблица результатов.
- [ ] Экран **таймлайна**: вертикальная шкала, дельты времени, статусы, раскрываемый `detail`.
- [ ] Вкладки или секции: «Сводка», «JSON» (read-only viewer).
- [ ] Обработка пустого результата и ошибок API.
- [ ] Конфигурация base URL API через env на сборке.
- [ ] (Опционально) Dockerfile и сервис в `docker-compose` для локальной разработки.

---

## Фаза 7 — OpenTelemetry и логи (опционально)

- [ ] Подключить `opentelemetry-instrumentation-aio-pika` в parser и processor.
- [ ] Экспорт в OTLP (Tempo/Jaeger); сохранять `trace_id` в событии или в `detail`.
- [ ] В UI добавить ссылку «Открыть в Grafana/Jaeger» по `otel_trace_id`.
- [ ] Структурировать логи с полем `correlation_id` для Loki; документировать запросы в Grafana Explore.

---

## Фаза 8 — Эксплуатация и качество

- [ ] Нагрузочный прогон: влияние `emit_event` на latency процессора.
- [ ] Политика **vacuum**/партиционирование по `occurred_at` при росте таблицы.
- [ ] Runbook для дежурных: как искать трейс, что делать при пустой цепочке.
- [ ] Обновить `docs/message-observability-architecture.md` при существенных отклонениях от плана.

---

## Быстрый MVP (минимальный вертикальный срез)

Если нужно ускорить ценность, выполнить в первую очередь:

1. Фаза 1 (минимум одна таблица + writer).
2. Фазы 2–3: `correlation_id` + 5–7 ключевых событий в processor.
3. Фаза 5: один эндпоинт `GET /internal/traces/{correlation_id}`.
4. Фаза 6: одна страница таймлайна без расширенного поиска.

Остальное — итерациями.
