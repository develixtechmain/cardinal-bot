# app/src/utils

## Назначение

Утилиты и константы приложения.

## Файлы

### api.ts — HTTP-утилита
- `authFetch(service, input, init?)` — обёртка над fetch с:
  - Автоматической инъекцией Bearer-токена
  - Обработкой 401 (refresh token)
  - Маршрутизацией на нужный сервис (backend / ai_core)

### consts.ts — Константы
- `SERVICE_LOCATOR` — URLs сервисов (backend, ai_core)
- `TARIFF_PRICES` — тарифы: {1: 4900, 3: 12500, 12: 42000} ₽
- `tools` — конфигурация инструментов (Finder, Contact Catcher)
- `actionButtons` — кнопки действий (Подписка, Рефералы)
- `subscriptionBenefits` — описание преимуществ подписки

### color.ts — Утилиты для работы с цветами

### date.ts — Парсинг и форматирование дат

### text.ts — Работа с текстом
