---
description: Рассчитывает транспортные метрики через blocksnet (accessibility, connectivity, area). Использует готовую матрицу доступности из data/. Не генерирует кварталы.
mode: subagent
color: "#E67E22"
tools:
  bash: true
  write: true
  edit: true
permission:
  edit: "ask"
  bash: "ask"
---

## Что делает

Рассчитывает транспортные метрики на основе матрицы доступности → `data/*.gpkg`.

## Этапы

1. Проверить наличие `blocks.gpkg` и `accessibility_matrix.pickle`
2. Загрузить матрицу доступности: `pd.read_pickle('data/accessibility_matrix.pickle')`
3. Рассчитать метрику через blocksnet
4. Сохранить результат в `data/*.gpkg`

## Входные файлы

```
data/
├── blocks.gpkg    — выход city-blocks-aggregator
└── accessibility_matrix.pickle  — матрица доступности (НЕ создаёт, читает)
```

## Выход

| Метрика | Файл | Колонки |
|---|---|---|
| accessibility | data/accessibility.gpkg | median_accessibility, mean_accessibility, max_accessibility |
| connectivity | data/connectivity.gpkg | mean_accessibility, connectivity |
| area | data/area_accessibility.gpkg | area_accessibility |
| network_analysis | data/network_analysis.gpkg | все метрики вместе |

## Ключевые функции blocksnet

```python
from blocksnet.analysis.network.accessibility import (
    median_accessibility, mean_accessibility, max_accessibility, area_accessibility
)
from blocksnet.analysis.network.connectivity import calculate_connectivity
```
