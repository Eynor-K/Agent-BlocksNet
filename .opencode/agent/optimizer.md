---
description: Оптимизирует наполнение сервисами для конкретного квартала на основе его land_use. Пользователь указывает block_id и land_use. Агент предлагает оптимальную ёмкость для всех сервисов в этом квартале.
mode: subagent
color: "#9B59B6"
tools:
  bash: true
  write: true
  edit: true
permission:
  edit: "ask"
  bash: "ask"
---

## Что делает

Оптимизирует наполнение сервисами для конкретного квартала на основе его (или нового) land_use. Использует TPE-алгоритм для поиска оптимальной ёмкости каждого сервиса.

## Этапы

1. Проверить наличие `blocks.gpkg` и `acc_mx.pickle`
2. Найти квартал по block_id и получить его land_use, либо применить новый land_use, переданный пользователем.
3. Определить допустимые сервисы по новому land_use из `blocksnet.config.service_types_config`.
4. Настроить TPE optimizer через `AreaSolution` и `Facade` (указать `blocks_lu` только для целевого квартала).
5. Запустить TPE optimizer для оптимизации сервисов для выбранного квартала.
6. Выгрузить результат в DataFrame через `facade.solution_to_services_df(best_x)`.
7. Сохранить результат в GPKG с геометрией квартала.

## Входные файлы

```
data/
├── blocks.gpkg    — выход city-blocks-aggregator
└── acc_mx.pickle  — матрица доступности
```

## Параметры (от пользователя)

- `block_id` — ID квартала
- `land_use` — тип land_use (новый или текущий). Обязательно конвертируется в `blocksnet.enums.LandUse`.

## Выход

`data/optimization_block_<block_id>.gpkg` — оптимальная ёмкость для каждого сервиса в квартале:
- block_id
- service_type
- capacity (оптимальная ёмкость)
- site_area
- build_floor_area
- count

## Пример использования инструментов (Python Pipeline)

Агент может запустить скрипт `agents/optimizer/runner.py` (если он обновлен) или создать собственный Python-скрипт с таким пайплайном, основанным на `area_based_tpe`:

```python
import geopandas as gpd
import pandas as pd
from blocksnet.optimization.services import (
    TPEOptimizer, WeightedObjective, WeightedConstraints,
    Facade, AreaSolution, RandomOrder, GradientChooser
)
from blocksnet.config import service_types_config
from blocksnet.enums import LandUse

# 1. Загрузка данных
blocks = gpd.read_file('data/blocks.gpkg')
blocks = blocks.to_crs(blocks.estimate_utm_crs())
acc_mx = pd.read_pickle('data/acc_mx.pickle')
blocks['site_area'] = blocks.area

# 2. Определение параметров квартала
block_id = 123  # задается пользователем
target_land_use_str = 'BUSINESS' # задается пользователем
target_land_use_enum = LandUse[target_land_use_str]

# Индекс квартала
block_idx = blocks[blocks['block_id'] == block_id].index[0]
blocks_lu = {block_idx: target_land_use_enum}

# 3. Инициализация Фасада и переменных
var_adapter = AreaSolution(blocks_lu)
facade = Facade(
    blocks_lu=blocks_lu,
    blocks_df=blocks,
    accessibility_matrix=acc_mx,
    var_adapter=var_adapter,
)

# 4. Добавление сервисов
available_services = service_types_config.get(target_land_use_enum, [])
service_weights = {service: 1.0 for service in available_services}

for service_type in available_services:
    col_name = f'capacity_{service_type}'
    if col_name in blocks.columns:
        caps = blocks[[col_name]].fillna(0).rename(columns={col_name: 'capacity'})
    else:
        caps = pd.DataFrame({'capacity': [0.0] * len(blocks)}, index=blocks.index)
    facade.add_service_type(service_type, 1.0, caps)

# 5. Оптимизация
objective = WeightedObjective(num_params=facade.num_params, facade=facade, weights=service_weights, max_evals=100)
constraints = WeightedConstraints(num_params=facade.num_params, facade=facade, priority=service_weights)

tpe_optimizer = TPEOptimizer(
    objective=objective, 
    constraints=constraints, 
    vars_order=RandomOrder(), 
    vars_chooser=GradientChooser(facade, num_params=facade.num_params, num_top=5)
)

best_x, best_val, perc, func_evals = tpe_optimizer.run(max_runs=100, timeout=300, initial_runs_num=1)

# 6. Извлечение и сохранение результата
solution_df = facade.solution_to_services_df(best_x)
target_geometry = blocks.loc[block_idx].geometry
solution_gdf = gpd.GeoDataFrame(solution_df, geometry=[target_geometry] * len(solution_df), crs=blocks.crs)

solution_gdf.to_file(f'data/optimization_block_{block_id}.gpkg', driver='GPKG')
print(f"Оптимизация завершена. Результат сохранен в data/optimization_block_{block_id}.gpkg")
```
