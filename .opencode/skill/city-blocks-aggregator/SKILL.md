---
name: city-blocks-aggregator
description: Генерирует кварталы, агрегирует здания и сервисы в blocks.gpkg. Не занимается анализом.
compatibility: opencode
metadata:
  audience: urban planners, GIS analysts
  workflow: block generation
---

## Этот скилл

Генерирует пространственную модель города.

**Делает:**
- Кварталы из дорог/границ
- Функциональные зоны (land use)
- Агрегация зданий
- Агрегация POI сервисов

**НЕ делает:**
- Транспортный анализ
- Граф улично-дорожной сети
- Изохроны, доступность, связность
- НЕ создаёт матрицу доступности (acc_mx)

## Пайплайн

1. `osmnx.geocode_to_gdf` → границы города
2. Загрузка `roads`, `water`, `railways` → фильтрация по BC_TAGS
3. `cut_urban_blocks` → слой кварталов
4. `assign_land_use` → функциональные зоны
5. `impute_buildings` + `aggregate_objects` → метрики зданий
6. Цикл по `data/platform/*.geojson` → `impute_services` + `aggregate_objects`
7. Сохранение → `data/blocks.gpkg`

## Выход

`data/blocks.gpkg` с колонками: geometry, land_use, building_metrics, service_metrics.
