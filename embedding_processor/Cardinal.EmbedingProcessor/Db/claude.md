# Db

## Назначение

Entity Framework Core — слой данных.

## Файлы

### AppDbContext.cs
- EF Core DbContext для PostgreSQL (Npgsql)
- Настройка таблицы `Recommendations` с индексом по TaskId
- Конвертер для хранения `List<Guid>` как CSV-строки

### Models/
- **Recommendation.cs** — модель рекомендации:
  - `Id` (Guid, PK) — уникальный идентификатор
  - `TaskId` (Guid) — привязка к задаче
  - `Vectors` (List&lt;Guid&gt;) — список ID векторов, показанных пользователю
  - `CreatedAt` (DateTime) — время создания
