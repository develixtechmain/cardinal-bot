# Security

## Назначение

Аутентификация API-запросов.

## Файлы

### ApiKeyAuthFilter.cs
- Глобальный фильтр авторизации (`IAsyncAuthorizationFilter`)
- Проверяет заголовок `X-API-KEY` во всех запросах
- Возвращает 401 Unauthorized при отсутствии или несовпадении ключа
- Ключ настраивается в `appsettings.json` → `ApiKey`
