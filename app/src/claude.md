# app/src

## Назначение

Исходный код React-приложения.

## Структура

| Директория | Назначение |
|---|---|
| [`api/`](api/claude.md) | Функции для запросов к бэкенду и AI Core |
| [`assets/`](assets/claude.md) | Импортируемые ресурсы (шрифты, иконки, SVG) |
| [`components/`](components/claude.md) | React-компоненты |
| [`pages/`](pages/claude.md) | Компоненты страниц (роуты) |
| [`store/`](store/claude.md) | Zustand-стейт менеджмент |
| [`types/`](types/claude.md) | TypeScript типы и интерфейсы |
| [`utils/`](utils/claude.md) | Утилиты и константы |

### Корневые файлы

| Файл | Назначение |
|---|---|
| `main.tsx` | Точка входа: React root |
| `App.tsx` | Роутер, инициализация (auth, загрузка user/subscription), ProtectedRoute |
| `global-styles.css` | Глобальные стили: шрифты, CSS-переменные, тёмная тема (#070707) |
| `vite-env.d.ts` | Типы для Vite |
