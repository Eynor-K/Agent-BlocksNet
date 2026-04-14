Sub-Agent: City Blocks Aggregator

Цель: выполнить пайплайн, собрать данные по блокам города и агрегировать их в файл blocks.gpkg.

Взаимодействие: агент может использовать библиотеку blocksnet-develop. Если она недоступна, агент падается на локальную агрегацию через geopandas.

Запуск:
python agents/city_blocks_aggregator/runner.py --pipeline-dir ./pipeline --output blocks.gpkg

Структура:
- agents/
  +- city_blocks_aggregator/
     - runner.py
     - config.yaml
     - requirements.txt
     - README.md
- skills/
  - city_blocks_aggregator/ ...
