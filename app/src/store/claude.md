# app/src/store

## Назначение

Zustand-сторы — управление состоянием приложения.

## Файлы

### store.ts — Основной стор
- `user: User | undefined` — текущий пользователь
- `subscription: Subscription | undefined` — подписка пользователя

### auth.ts — Аутентификация
- `accessToken`, `refreshToken` — JWT-токены
- `clearTokens()` — очистка токенов + редирект на `/`
- `refreshAccessToken()` — обновление access-токена через refresh

### error.ts — Глобальные ошибки
- `type: "exception" | "subscription" | null` — тип ошибки
- `message`, `location` — детали
- Управляет модалками ошибок через GlobalModals

### finder.ts — Finder
- `tasks: FinderTask[]` — список задач пользователя
- `tasksStats` — статистика по задачам
- CRUD-операции для задач

### questions.ts — Брифинг (онбординг)
- `id` — ID сессии онбординга
- `answers: Answer[]` — ответы пользователя
- `additionalQuestions` — дополнительные вопросы от AI
- `baseQuestions[]` — 6 базовых вопросов
- `specialists` — Map из 55+ типов специалистов с ключевыми словами

### referral.ts — Рефералы
- `refs: RefUser[]` — список рефералов
