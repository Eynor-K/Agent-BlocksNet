# Urban AI Agents: Agent-BlocksNet

**Agent-BlocksNet** — это мультиагентная система для автоматизированного урбанистического моделирования и анализа. Проект построен на базе фреймворка [OpenCode](https://opencode.ai/) и использует библиотеку [blocksnet](https://github.com/iduprojects/blocksnet) для комплексных вычислений.

---

## 🏗 Архитектура

Система состоит из главного агента-оркестратора и нескольких специализированных подагентов, каждый из которых отвечает за свой домен:

```text
master-urban-planner (Primary Orchestrator)
    ├── city-blocks-aggregator     ← пространственная модель города
    ├── transport-analytics        ← транспортная и пешеходная доступность
    └── optimizer                  ← оптимизация размещения сервисов
```

Все агенты имеют строгое разделение логики и зон ответственности.

### 1. Master Urban Planner (Главный оркестратор)
Роль: Принимает запросы пользователя и маршрутизирует их на нужных подагентов. Сам не выполняет вычисления, но следит за наличием необходимых артефактов (например, `blocks.gpkg` или `acc_mx.pickle`) перед запуском зависимых анализов.

### 2. City Blocks Aggregator
Роль: Генерирует пространственную модель города.
- Вырезает кварталы на основе дорожной сети и границ.
- Назначает функциональные зоны (`land_use`).
- Агрегирует здания (площадь, население) и сервисы (POI).
- Сохраняет результат в `data/blocks.gpkg`.

### 3. Transport Analytics
Роль: Рассчитывает транспортные метрики кварталов (доступность и связность).
- **Accessibility:** расчет медианной, средней и максимальной доступности (`data/accessibility.gpkg`).
- **Connectivity:** расчет транспортной связности (`data/connectivity.gpkg`).
- **Area:** расчет площадной доступности (`data/area_accessibility.gpkg`).
- **Network Analysis:** расчет всех метрик разом (`data/network_analysis.gpkg`).

### 4. Optimizer
Роль: Оптимизирует размещение городских сервисов внутри конкретного квартала.
- Использует TPE-алгоритм (Tree-structured Parzen Estimator) через библиотеку Optuna.
- Принимает на вход `block_id` и опционально новый `land_use`.
- Вычисляет оптимальную емкость сервисов для заданного квартала и возвращает `data/optimization_block_<block_id>.gpkg`.

---

## 🚀 Быстрый запуск

Убедитесь, что в директории `data/` находятся необходимые исходные данные (если они требуются для выбранного этапа).
Для запуска скриптов напрямую в Windows используйте команду `py -3`.

**1. Создание модели города:**
```bash
py -3 agents/city_blocks_aggregator/runner.py --data-dir data --city Урай --output data/blocks.gpkg
```

**2. Полный транспортный анализ:**
```bash
py -3 agents/transport_analytics/runner.py --blocks data/blocks.gpkg --acc-mx data/acc_mx.pickle --metric network_analysis
```

**3. Анализ отдельных метрик:**
```bash
py -3 agents/transport_analytics/runner.py --blocks data/blocks.gpkg --acc-mx data/acc_mx.pickle --metric accessibility
py -3 agents/transport_analytics/runner.py --blocks data/blocks.gpkg --acc-mx data/acc_mx.pickle --metric connectivity
py -3 agents/transport_analytics/runner.py --blocks data/blocks.gpkg --acc-mx data/acc_mx.pickle --metric area
```

**4. Оптимизация сервисов в квартале:**
```bash
py -3 agents/optimizer/runner.py --blocks data/blocks.gpkg --acc-mx data/acc_mx.pickle --land-use BUSINESS --block-id 123
```

---

## 🛠 Зависимости и структура

- `.opencode/` — конфигурации, команды, скиллы и описания агентов для фреймворка OpenCode.
- `agents/` — исходный код пайплайнов для генерации кварталов, транспорта и оптимизации (runner-скрипты, конфиги, requirements).
- `data/` — рабочая папка (игнорируется в git), в которой должны лежать матрицы `acc_mx.pickle` и сохраняются выходные GeoPackage-файлы (`.gpkg`).

---

## 🤖 Использование через OpenCode
Вы можете запускать проект через CLI или TUI интерфейс OpenCode. Агент `master-urban-planner` сам подберет нужный скилл в зависимости от вашего промпта:
- *"Создай модель города Екатеринбург"*
- *"Сделай транспортный анализ"*
- *"Посчитай connectivity для текущего города"*
- *"Оптимизируй сервисы для квартала 42 под BUSINESS"*
