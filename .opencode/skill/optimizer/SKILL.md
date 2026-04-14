---
name: optimizer
description: Оптимизирует наполнение сервисами для квартала на основе (в том числе нового) land_use. Использует TPE для поиска оптимальной ёмкости всех сервисов.
compatibility: opencode
metadata:
  audience: urban planners
  workflow: service optimization
---

## Этот скилл

Оптимизирует наполнение сервисами для конкретного квартала.

**Делает:**
- Находит квартал по `block_id`
- Определяет `land_use` квартала (или принимает новый `land_use` от пользователя)
- Находит допустимые сервисы по `land_use` из `blocksnet.config`
- Подготавливает данные (`AreaSolution`, `Facade`) для TPE
- Запускает TPE-оптимизатор для поиска оптимальной вместимости всех разрешенных сервисов
- Извлекает результат через `facade.solution_to_services_df()` и возвращает оптимальную ёмкость для каждого сервиса, объединяя с геометрией квартала.

**НЕ делает:**
- Генерацию кварталов
- Транспортный анализ

## Вход

- `data/blocks.gpkg`
- `data/acc_mx.pickle`
- `block_id` (от пользователя)
- `land_use` (опционально, иначе берётся из block)

## Выход

`data/optimization_block_<block_id>.gpkg` — оптимальная ёмкость для каждого сервиса:
- block_id
- service_type
- capacity
- count
- site_area
- build_floor_area
- geometry

## Пример пайплайна (на базе area_based_tpe)

Для выполнения оптимизации вы можете использовать встроенный скрипт `agents/optimizer/runner.py`, передав нужные аргументы, например:
```bash
python agents/optimizer/runner.py --blocks data/blocks.gpkg --acc-mx data/acc_mx.pickle --block-id 123 --land-use BUSINESS
```

Или можете создать собственный python-скрипт с аналогичной логикой:

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
```
