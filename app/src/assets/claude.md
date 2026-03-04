# app/src/assets

## Назначение

Ресурсы, импортируемые в код (обрабатываются Vite).

## Структура

| Директория | Содержимое |
|---|---|
| `fonts/` | Шрифты: Anonymous Pro, Organetto, SF UI Display (8 файлов) |
| `icons/` | SVG-иконки: mark, empty-mark, info, eagle и др. |
| `finder/` | SVG для инструмента Finder (action-task, add-task, selector) |
| `contact-catcher/` | SVG для Contact Catcher (selector, selection) |
| `subscription/` | SVG для страницы подписки (header, features-background) |

SVG-файлы импортируются как React-компоненты через SVGR плагин.
