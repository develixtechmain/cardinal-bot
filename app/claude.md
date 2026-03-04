# app

## Назначение

Telegram Mini App — фронтенд-приложение Cardinal. Интерфейс для управления задачами поиска лидов, подписками и реферальной программой.

## Технологии

- React 19.1, TypeScript 5.8
- Vite 5.4 (сборка)
- Zustand 5.0 (состояние)
- Wouter 3.7 (роутинг)
- CSS Modules (стили)
- SVGR (SVG → React компоненты)
- Telegram Web App SDK

## Структура

| Директория | Назначение |
|---|---|
| [`src/`](src/claude.md) | Исходный код приложения |
| [`public/`](public/claude.md) | Статические ресурсы |

### Корневые файлы

| Файл | Назначение |
|---|---|
| `index.html` | HTML entry point (подключает Telegram Web App SDK) |
| `package.json` | Зависимости и скрипты |
| `vite.config.ts` | Конфигурация Vite (React, SVGR, HTTPS) |
| `tsconfig.json` | TypeScript: ES2022, strict, react-jsx |
| `Dockerfile` | Контейнеризация |

## Скрипты

| Команда | Действие |
|---|---|
| `npm run dev` | Vite dev server + CSS types watcher |
| `npm run build` | Генерация CSS types → Vite build |
| `npm run start` | Serve dist/ на порту 5173 |

## Маршруты

```
/                              → Главная (дашборд)
/subscription                  → Страница подписки
/subscription/purchase/:months → Покупка подписки
/subscription/trial-used       → Trial истёк
/finder                        → Finder (инструмент)
/finder/tasks                  → Список задач
/finder/briefing/*             → Онбординг (alert → questions → verify → completed)
/referral                      → Реферальная программа
```

## Переменные окружения

| Переменная | Описание |
|---|---|
| `VITE_BACKEND_BASE_URL` | URL бэкенда |
| `VITE_AI_CORE_BASE_URL` | URL AI Core |
| `VITE_USE_HTTPS` | Включить HTTPS (dev) |
