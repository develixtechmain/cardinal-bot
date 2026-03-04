# Cardinal.EmbedingProcessor

## Назначение

ASP.NET Core 9.0 Web API приложение для управления векторными эмбеддингами и семантического поиска.

## Структура поддиректорий

### Controllers/
API-контроллеры:
- **VectorsController** — создание эмбеддингов из тегов, удаление по задаче, семантический поиск
- **LearningController** — feedback loop: отметка success/fail для рекомендаций
- **RecommendationsController** — сохранение факта выдачи рекомендации

### Db/
Entity Framework Core:
- **AppDbContext.cs** — контекст БД, конфигурация таблицы Recommendations
- **Models/Recommendation.cs** — модель: Id, TaskId, Vectors (CSV список GUID), CreatedAt

### Dtos/
Data Transfer Objects (15 файлов):
- Запросы: `CreateTagVectorsRequestDto`, `SearchMessageRequest`, `ConfirmRecommendationRequest`
- Ответы: `SearchResponseItemDto`, `SearchResponseTagDto`, `EmbeddingResponseDto`
- Qdrant: `QdrantPayload`, `QdrantPointDto`, `QdrantSearchResponse` и др.

### Migrations/
EF Core миграции для PostgreSQL.

### Security/
- **ApiKeyAuthFilter.cs** — глобальный фильтр авторизации по заголовку `X-API-KEY`

### Properties/
- **launchSettings.json** — настройки запуска для разработки

## Ключевые утилиты

- **TextSplitter.cs** — разбиение текста на чанки через sliding window (256 токенов, stride 128)
- **VectorPooler.cs** / **VectorPooling.cs** — объединение множества эмбеддингов в один вектор (mean/max pooling)

## Конфигурация (appsettings.json)

| Секция | Параметры |
|---|---|
| ConnectionStrings.Postgres | Строка подключения к PostgreSQL |
| Qdrant | Host, CollectionName ("leads"), ApiKey |
| EmbeddingsApi | Host HF Text Embeddings сервиса |
| Search | TopN=1000, ScoreThreshold=0.838, BayesianAlpha/Beta=1.0, PoolingMode="max" |
| ApiKey | Ключ для аутентификации запросов |
