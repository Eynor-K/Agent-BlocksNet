---
name: master-urban-planner
description: Главный скилл-оркестратор. Понять запрос и вызвать нужного суб-агента. city-blocks-aggregator или transport-analytics — строго по одному.
compatibility: opencode
metadata:
  audience: urban planners, data analysts
  workflow: task routing
---

## Этот скилл

Единственная задача — маршрутизация. Понять запрос → вызвать нужного агента. Не выполнять самому.

## Проверка перед запуском

**transport-analytics:**
- СНАЧАЛА проверь: существует ли `data/blocks.gpkg`?
- Если НЕТ → сначала вызови city-blocks-aggregator
- Если ДА → запускай transport-analytics

## Два агента — ноль пересечений

### city-blocks-aggregator
ЗАДАЧА: модель города (кварталы, здания, сервисы)
ВЫХОД: `data/blocks.gpkg`
ВЫЗЫВАТЬ КОГДА: "модель", "кварталы", "здания", "сервисы"

### transport-analytics
ЗАДАЧА: транспорт через blocksnet (accessibility, connectivity, area)
ВХОД: `data/blocks.gpkg` + `data/acc_mx.pickle`
ВЫХОД: `data/transport.gpkg` (отдельный файл)
ВЫЗЫВАТЬ КОГДА: "транспорт", "доступность", "accessibility", "connectivity", "area"
ВАЖНО: Не создаёт acc_mx — читает из data/

## Схема маршрутизации

```
Запрос
  ├── содержит "модель"/"кварталы"/"здания" → city-blocks-aggregator
  ├── содержит "транспорт"/"accessibility" → transport-analytics
  ├── содержит оба → оба (сначала city-blocks, потом transport)
  └── неясно → спросить пользователя
```

## Метрики transport-analytics

| Метрика | Параметр --metric | Выходной файл |
|---|---|---|
| accessibility | accessibility | data/accessibility.gpkg |
| connectivity | connectivity | data/connectivity.gpkg |
| area | area | data/area_accessibility.gpkg |
| network_analysis | network_analysis | data/network_analysis.gpkg |

## Примеры

| Запрос | Действие |
|---|---|
| "построй модель Урая" | city-blocks-aggregator |
| "рассчитай доступность" | transport (metric=accessibility) |
| "рассчитай connectivity" | transport (metric=connectivity) |
| "рассчитай area accessibility" | transport (metric=area) |
| "модель + транспорт" | оба (сначала city-blocks) |
| "что нужно сделать?" | уточнить у пользователя |
