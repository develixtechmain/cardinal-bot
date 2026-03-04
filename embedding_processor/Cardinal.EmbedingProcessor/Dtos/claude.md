# Dtos

## Назначение

Data Transfer Objects — модели запросов и ответов API.

## Запросы
- **CreateTagVectorsRequestDto** — создание эмбеддингов: Tags[], TaskId, UserId
- **SearchMessageRequest** — поиск: Message (текст)
- **ConfirmRecommendationRequest** — подтверждение рекомендации: RecommendationId, SubmittedTaskId, SubmittedVectors

## Ответы
- **SearchResponseItemDto** — результат поиска: TaskId, UserId, Score, Tags[]
- **SearchResponseTagDto** — тег в результате: Id, Text
- **EmbeddingResponseDto** — ответ от HF: Embeddings (float[][])

## Qdrant DTO
- **QdrantPayload** — метаданные вектора: TaskId, UserId, Tag, SuccessCount, FailCount
- **QdrantPointDto** — точка: Id, Version, Score, Payload
- **QdrantSearchResponse** — ответ поиска: Result[]
- **QdrantPointsByIdsResponseDto** — точки по ID: Result[]
- **QdrantSetPayloadOperation** — обновление payload: Points[], Payload
