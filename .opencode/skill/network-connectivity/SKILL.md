---
name: network-connectivity
description: Рассчитывает метрики связности на основе матрицы доступности из blocksnet. Не генерирует кварталы.
compatibility: opencode
metadata:
  audience: transport planners
  workflow: network analysis
---

## Этот скилл

Рассчитывает connectivity (связность) на основе матрицы доступности blocksnet.

**Делает:**
- mean_accessibility → connectivity = 1/accessibility

**НЕ делает:**
- Генерацию кварталов
- Агрегацию зданий/сервисов

## Вход

- `data/blocks.gpkg` — должен существовать
- `data/acc_mx.pickle` — матрица доступности

## Выход

`data/connectivity.gpkg` с колонками:
- geometry
- mean_accessibility
- connectivity
