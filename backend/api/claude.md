# backend/api

## Назначение

FastAPI-роутеры — REST API эндпоинты бэкенда.

## Файлы

### auth.py — Аутентификация (`/api/auth`)
| Метод | Путь | Описание |
|---|---|---|
| POST | `/api/auth` | Логин через Telegram Web App (init_data + HMAC-SHA256) |
| POST | `/api/auth/refresh` | Обновление JWT-токенов |

Поддерживает реферальные коды из `start_param`.

### users.py — Профиль пользователя (`/api/users`)
| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/users/me` | Получить профиль текущего пользователя |
| PATCH | `/api/users/me` | Обновить username/avatar |

### finder.py — Управление задачами и рекомендациями (`/api/finder`)
| Метод | Путь | Auth | Описание |
|---|---|---|---|
| GET | `/api/finder/tasks/me` | JWT | Список задач пользователя со статистикой |
| GET | `/api/finder/tasks/stats` | JWT | Агрегированная статистика |
| POST | `/api/finder/tasks` | JWT | Создать задачу (макс. 5 на пользователя) |
| PATCH | `/api/finder/tasks/{id}` | JWT | Вкл/выкл задачу |
| DELETE | `/api/finder/tasks/{id}` | JWT | Удалить задачу |
| GET | `/api/finder/channels` | JWT | Каналы пользователя |
| DELETE | `/api/finder/channels/{id}` | JWT | Отвязать канал |
| POST | `/api/finder/recommendations/send` | API Key | Отправить рекомендацию (внутренний) |

### subscriptions.py — Подписки и платежи (`/api/subscriptions`)
| Метод | Путь | Auth | Описание |
|---|---|---|---|
| GET | `/api/subscriptions/me` | JWT | Статус подписки |
| POST | `/api/subscriptions/{id}/trial` | JWT | Активировать 3-дневный пробный период |
| POST | `/api/subscriptions/purchase` | JWT | Инициировать покупку (Lava/Alpha/Balance) |
| GET | `/api/subscriptions/purchase/{trxId}` | JWT | Проверить статус транзакции |
| GET | `/api/subscriptions/purchase/complete` | — | Callback после оплаты (HTML) |
| POST | `/api/subscriptions/purchase/balance` | JWT | Оплата с баланса (1 мес.) |
| DELETE | `/api/subscriptions/recurrency` | JWT | Отключить автоплатёж |
| POST | `/api/subscriptions/webhook/lava` | API Key | Webhook от Lava.top |

### refs.py — Реферальная система (`/api/refs`)
| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/refs/me` | Список рефералов |
| GET | `/r/{user_id}` | Реферальная ссылка → редирект в Telegram |
