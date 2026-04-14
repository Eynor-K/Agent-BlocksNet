---
name: area-accessibility
description: Рассчитывает площадную доступность на основе матрицы доступности и площадей кварталов из blocksnet. Не генерирует кварталы.
compatibility: opencode
metadata:
  audience: transport planners
  workflow: network analysis
---

## Этот скилл

Рассчитывает area_accessibility — площадную доступность с учётом площади кварталов.

**Делает:**
- area_accessibility = weighted by site_area

**НЕ делает:**
- Генерацию кварталов
- Агрегацию зданий/сервисов

## Вход

- `data/blocks.gpkg` — должен существовать (нужна колонка site_area)
- `data/acc_mx.pickle` — матрица доступности

## Выход

`data/area_accessibility.gpkg` с колонками:
- geometry
- area_accessibility
