---
name: network-accessibility
description: Рассчитывает метрики доступности (median, mean, max) на основе матрицы доступности из blocksnet. Не генерирует кварталы.
compatibility: opencode
metadata:
  audience: transport planners
  workflow: network analysis
---

## Этот скилл

Рассчитывает транспортные метрики доступности из матрицы доступности blocksnet.

**Делает:**
- median_accessibility — медианная доступность
- mean_accessibility — средняя доступность
- max_accessibility — максимальная доступность

**НЕ делает:**
- Генерацию кварталов
- Агрегацию зданий/сервисов

## Вход

- `data/blocks.gpkg` — должен существовать
- `data/acc_mx.pickle` — матрица доступности

## Выход

`data/accessibility.gpkg` с колонками:
- geometry
- median_accessibility
- mean_accessibility
- max_accessibility
