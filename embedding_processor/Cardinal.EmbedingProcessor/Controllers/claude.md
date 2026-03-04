# Controllers

## Назначение

ASP.NET Core API-контроллеры Embedding Processor.

## Контроллеры

### VectorsController (`/api/vectors`)
- **POST `/api/vectors/tags`** — создать эмбеддинги для массива тегов (привязка к TaskId, UserId), сохранить в Qdrant
- **DELETE `/api/vectors/by-task/{taskId}`** — удалить все векторы задачи из Qdrant
- **POST `/api/vectors/search`** — семантический поиск: sliding window токенизация → эмбеддинг → pooling → Qdrant search → байесовское ранжирование → группировка по TaskId

### LearningController (`/api/learning`)
- **PATCH `/api/learning/{id}/success`** — увеличить success_count векторов рекомендации в Qdrant
- **PATCH `/api/learning/{id}/fail`** — увеличить fail_count векторов рекомендации в Qdrant

### RecommendationsController (`/api/recommendation`)
- **POST `/api/recommendation/confirm`** — записать факт выдачи рекомендации (RecommendationId, TaskId, Vectors) в PostgreSQL
