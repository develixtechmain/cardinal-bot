# app/src/pages

## Назначение

Компоненты страниц (маршруты приложения).

## Структура

### Корневые страницы
Главные страницы приложения: Home, Subscription, Referral и др.

### finder/ — Страницы Finder
| Файл/Директория | Маршрут | Назначение |
|---|---|---|
| Finder page | `/finder` | Главная страница инструмента |
| Tasks page | `/finder/tasks` | Список задач |
| `briefing/` | `/finder/briefing/*` | Онбординг-воронка |

### finder/briefing/ — Онбординг
Пошаговый процесс создания задачи:

| Шаг | Маршрут | Описание |
|---|---|---|
| Alert | `/finder/briefing/alert` | Вступительный экран |
| Questions | `/finder/briefing/questions` | Основные вопросы |
| Additional | `/finder/briefing/questions/additional` | Дополнительные вопросы от AI |
| Verify | `/finder/briefing/verify` | Проверка ответов |
| Completed | `/finder/briefing/completed` | Завершение → title + tags |
