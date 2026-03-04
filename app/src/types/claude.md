# app/src/types

## Назначение

TypeScript-определения типов (.d.ts файлы).

## Файлы

### index.d.ts — Основные типы
- **User** — профиль: id, user_id, first_name, last_name, username, avatar_url, balance, referrer_id, tg (WebAppUser)
- **Subscription** — подписка: trial_starts_at, trial_ends_at, subscription_ends_at + методы (daysLeft, isActive, isTrialUsed, isSubscriptionExpired)
- **Tool** — инструмент: id ("finder" | "contact-catcher"), title, subtitle, description, url, color
- **ActionButton** — кнопка действия: buttonLabel, color, url

### finder/index.d.ts — Типы Finder
- **Question** — вопрос брифинга: question, description, selection, examples(), hint
- **Answer** — ответ: text, selections (Set)
- **QuestionAnswer** — пара вопрос-ответ
- **FinderTask** — задача: id, title, tags[], active, created_at
- **FinderTaskStatistics** — статистика: avg, total, today
- **RefUser** — реферал: id, username, avatar_url, billed
