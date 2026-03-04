# app/src/api

## Назначение

Слой API — функции для HTTP-запросов к бэкенду и AI Core.

## Файлы

### base.ts — Основные запросы (Backend)
- `fetchUser()` — GET `/users/me`
- `patchUser(user)` — PATCH `/users/me`
- `fetchSubscription()` — GET `/subscriptions/me`
- `startSubscriptionTrial(subId)` — POST `/subscriptions/{id}/trial`
- `fetchPurchase(months, bank, email)` — POST `/subscriptions/purchase`
- `checkPurchase(trxId)` — GET `/subscriptions/purchase/{id}`
- `purchaseFromBalance()` — POST `/subscriptions/purchase/balance`

### briefing.ts — Онбординг (AI Core)
- `fetchBriefing(userId)` — POST `/onboarding/start`
- `answerQuestions(briefingId, answers)` — POST `/onboarding/{id}/answer`
- `completeBriefing(briefingId, totalAnswers)` — POST `/onboarding/{id}/complete`
- `createTask(cloudTask)` — POST `/finder/tasks` (Backend)

### finder.ts — Задачи (Backend)
- `fetchUserTasks()` — GET `/finder/tasks/me`
- `fetchUserTasksStats()` — GET `/finder/tasks/stats`
- `patchUserTask(task)` — PATCH `/finder/tasks/{id}`
- `deleteUserTask(taskId)` — DELETE `/finder/tasks/{id}`

### refs.ts — Рефералы (Backend)
- `fetchRefs()` — GET `/refs/me`

## Маршрутизация сервисов

Все запросы идут через `authFetch()` (из `utils/api.ts`), который:
- Добавляет Bearer-токен
- Автоматически обновляет токен при 401
- Маршрутизирует на нужный сервис (backend или ai_core)
