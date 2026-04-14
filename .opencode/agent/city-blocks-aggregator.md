---
description: Генерирует кварталы города, назначает функциональные зоны, агрегирует здания и сервисы в blocks.gpkg. НЕ занимается другим анализом.
mode: subagent
color: "#27AE60"
tools:
  bash: true
  write: true
  edit: true
permission:
  edit: "ask"
  bash: "ask"
---

## Что делает

Создаёт модель города: слой кварталов + здания + сервисы + функциональные зоны → `blocks.gpkg`.

## Этапы

1. Загрузить границы города через osmnx
2. Загрузить roads, water, railways из data/
3. Сгенерировать кварталы: `cut_urban_blocks`
4. Назначить функциональные зоны: `assign_land_use`
5. Агрегировать здания: `impute_buildings` + `aggregate_objects`
6. Агрегировать все POI из `data/platform/*.geojson`
7. Сохранить `data/blocks.gpkg`

## Входные файлы

```
data/
├── roads.geojson        — дорожная сеть
├── water.geojson       — водные объекты
├── railways.geojson     — железные дороги
├── terzones.geojson    — функциональные зоны
├── RULES_LU.json       — правила land use
├── buildings.gpkg      — здания
└── platform/
    └── *.geojson       — POI сервисы
```

## Выход

`data/blocks.gpkg` — агрегированные кварталы:
- geometry
- land_use
- метрики зданий (площадь, этажность, население)
- метрики сервисов (ёмкость POI по типам)

## Ключевые функции blocksnet

```python
from blocksnet.blocks.cutting import preprocess_urban_objects, cut_urban_blocks
from blocksnet.blocks.postprocessing import postprocess_urban_blocks
from blocksnet.blocks.assignment import assign_land_use
from blocksnet.blocks.aggregation import aggregate_objects
from blocksnet.preprocessing.imputing import impute_buildings, impute_services
from blocksnet.enums import LandUse
```
