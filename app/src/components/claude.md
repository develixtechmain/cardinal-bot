# app/src/components

## Назначение

React-компоненты приложения. Организованы по фичам + общие компоненты.

## Структура

### Общие компоненты (`common/`)
| Компонент | Назначение |
|---|---|
| [`Alert/`](common/Alert/claude.md) | Модалки ошибок, подписок, ErrorBoundary |
| `Header/` | Верхняя навигация |
| `Loading/` | Спиннер загрузки |
| `Buttons/` | WideButton (основная CTA), LearnMoreButton |
| `Delimiter/` | Визуальный разделитель |
| `BottomSection/` | Футер со ссылками |
| `AboutToolModal/` | Модалка информации об инструменте |
| `ToolSelection/` | Выбор инструмента (ToolSelectionModal, ToolSelector, ToolCard) |

### Компоненты главной страницы
| Компонент | Назначение |
|---|---|
| `ProfileSection/` | Профиль: имя, аватар, баланс, статус подписки |
| `ActionButtons/` | Кнопки "Подписка" и "Рефералы" |
| `ToolsSection/` | Сетка доступных инструментов |
| `SubscriptionAlert/` | Алерт о статусе подписки |
| `ClubSection/` | Секция сообщества/клуба |

### Компоненты по фичам
| Директория | Назначение |
|---|---|
| [`finder/`](finder/claude.md) | Компоненты инструмента Finder |
| `contact-catcher/` | Компоненты Contact Catcher (AboutModal) |
| [`subscription/`](subscription/claude.md) | Компоненты подписки |
| `referral/` | Компоненты реферальной системы |
