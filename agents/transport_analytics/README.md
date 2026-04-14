Transport Analytics Sub-Agent

Рассчитывает транспортные метрики через blocksnet.

Metrics (--metric):
- accessibility: median_accessibility, mean_accessibility, max_accessibility → data/accessibility.gpkg
- connectivity: mean_accessibility, connectivity → data/connectivity.gpkg
- area: area_accessibility → data/area_accessibility.gpkg
- network_analysis: все метрики вместе → data/network_analysis.gpkg

Run:
py -3 agents/transport_analytics/runner.py --blocks data/blocks.gpkg --acc-mx data/acc_mx.pickle --metric network_analysis
