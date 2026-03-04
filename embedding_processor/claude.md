# embedding_processor

## Назначение

Сервис семантического поиска и обучения на основе обратной связи. Преобразует текстовые теги в векторные эмбеддинги, хранит их в Qdrant, выполняет семантический поиск и улучшает качество рекомендаций через байесовское ранжирование.

## Технологии

- C# / ASP.NET Core 9.0
- Entity Framework Core 9.0 + Npgsql (PostgreSQL)
- Qdrant 1.15.4 (векторная БД)
- Hugging Face Text Embeddings Inference (модель intfloat/multilingual-e5-base)
- Docker

## Структура

```
Cardinal.EmbedingProcessor/
├── Controllers/         — API-контроллеры
├── Db/                  — EF Core контекст и модели
├── Dtos/                — DTO для запросов/ответов
├── Migrations/          — Миграции EF Core
├── Security/            — API Key фильтр
├── Program.cs           — Точка входа
├── appsettings.json     — Конфигурация
└── Dockerfile           — Контейнеризация
```

Подробнее о каждой поддиректории — см. [`Cardinal.EmbedingProcessor/claude.md`](Cardinal.EmbedingProcessor/claude.md).

## API-эндпоинты

| Метод | Путь | Описание |
|---|---|---|
| POST | `/api/vectors/tags` | Создать эмбеддинги для тегов задачи |
| DELETE | `/api/vectors/by-task/{taskId}` | Удалить векторы задачи |
| POST | `/api/vectors/search` | Семантический поиск по сообщению |
| PATCH | `/api/learning/{id}/success` | Отметить рекомендацию как успешную |
| PATCH | `/api/learning/{id}/fail` | Отметить рекомендацию как неуспешную |
| POST | `/api/recommendation/confirm` | Сохранить факт выдачи рекомендации |

## Алгоритм поиска

1. **Токенизация**: Sliding window (256 токенов, stride 128)
2. **Эмбеддинг**: HF Text Embeddings Inference → множество векторов
3. **Пулинг**: Mean или Max pooling → единый вектор
4. **Поиск**: Qdrant similarity search (порог 0.838, top 1000)
5. **Байесовское ранжирование**: `(α + success) / (α + β + success + fail)` × similarity
6. **Группировка**: По TaskId, фильтрация по минимальному порогу (0.6)

## Подключения

- **Входящие**: message_processor, backend (HTTP API)
- **Исходящие**: Qdrant, PostgreSQL, HF Embeddings service
