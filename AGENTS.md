# Urban AI Agents

Система агентов для урбанистического моделирования на базе OpenCode.

## Архитектура

```
master-urban-planner (primary)
    ├── city-blocks-aggregator     ← модель города (кварталы, здания, сервисы)
    ├── transport-analytics        ← транспорт (blocksnet метрики)
    │     ├── accessibility
    │     ├── connectivity
    │     ├── area
    │     └── network_analysis
    └── optimizer                   ← оптимизация сервисов (TPE)
```

**Разделение строгое. Агенты не пересекаются.**

## Агенты

### master-urban-planner
**Тип:** primary | **Цвет:** #4A90E2

Оркестратор. Маршрутизирует запрос → нужный агент. Не выполняет сам.
**Проверяет наличие blocks.gpkg и acc_mx.pickle перед запуском анализа/оптимизации.**

### city-blocks-aggregator
**Тип:** subagent | **Цвет:** #27AE60

Генерирует пространственную модель города:
- Кварталы из дорог/границ (`cut_urban_blocks`)
- Функциональные зоны (`assign_land_use`)
- Агрегация зданий (площадь, население)
- Агрегация POI сервисов
- **Выход:** `data/blocks.gpkg`

**НЕ делает:** транспортный анализ, матрицу доступности.

### transport-analytics
**Тип:** subagent | **Цвет:** #E67E22

Рассчитывает транспортные метрики через blocksnet:
- Использует готовую `acc_mx.pkl` (НЕ создаёт)
- **Вход:** `data/blocks.gpkg` + `data/acc_mx.pickle`
- **Выход:** `data/*.gpkg` (см. метрики ниже)

**НЕ делает:** генерацию кварталов, создание acc_mx, osmnx анализ.

### optimizer
**Тип:** subagent | **Цвет:** #9B59B6

Оптимизирует размещение сервисов внутри конкретного квартала:
- Пользователь указывает `block_id` и `land_use` (опционально, иначе текущий)
- Использует TPE-алгоритм из Optuna
- **Вход:** `data/blocks.gpkg` + `data/acc_mx.pickle` + block_id + land_use
- **Выход:** `data/optimization_block_<block_id>.gpkg`

## Метрики transport-analytics

| Метрика | Колонки | Выходной файл |
|---|---|---|
| accessibility | median_accessibility, mean_accessibility, max_accessibility | data/accessibility.gpkg |
| connectivity | mean_accessibility, connectivity | data/connectivity.gpkg |
| area | area_accessibility | data/area_accessibility.gpkg |
| network_analysis | все метрики вместе | data/network_analysis.gpkg |

## Маршрутизация

| Запрос | Агент |
|---|---|
| "построить модель города" | city-blocks-aggregator |
| "транспортный анализ" | transport-analytics (network_analysis) |
| "доступность/accessibility" | transport-analytics (accessibility) |
| "connectivity/связность" | transport-analytics (connectivity) |
| "area accessibility" | transport-analytics (area) |
| "оптимизируй сервисы для квартала" | optimizer (нужны block_id + land_use) |
| "модель + транспорт" | оба (последовательно) |
| blocks.gpkg нет | city-blocks-aggregator → анализ/оптимизация |
| неясно | спросить пользователя |

## Быстрый запуск

```bash
# Модель города
py -3 agents/city_blocks_aggregator/runner.py --data-dir data --city Урай --output data/blocks.gpkg

# Транспортный анализ (blocksnet)
py -3 agents/transport_analytics/runner.py --blocks data/blocks.gpkg --acc-mx data/acc_mx.pickle --metric network_analysis

# Отдельные метрики
py -3 agents/transport_analytics/runner.py --blocks data/blocks.gpkg --acc-mx data/acc_mx.pickle --metric accessibility
py -3 agents/transport_analytics/runner.py --blocks data/blocks.gpkg --acc-mx data/acc_mx.pickle --metric connectivity
py -3 agents/transport_analytics/runner.py --blocks data/blocks.gpkg --acc-mx data/acc_mx.pickle --metric area

# Оптимизация сервисов в квартале
py -3 agents/optimizer/runner.py --blocks data/blocks.gpkg --acc-mx data/acc_mx.pickle --land-use BUSINESS --block-id 123
```

**Примечание:** На Windows использовать `py -3` вместо `python`.
