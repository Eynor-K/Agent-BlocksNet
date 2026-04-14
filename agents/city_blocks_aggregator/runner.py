import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'blocksnet-develop'))

import logging
import argparse
import json


REQUIRED_FILES = [
    'roads.geojson',
    'buildings.gpkg',
    'terzones.geojson',
    'RULES_LU.json'
]

def validate_inputs(data_dir: str) -> list:
    """Валидация обязательных файлов."""
    missing = []
    for f in REQUIRED_FILES:
        filepath = os.path.join(data_dir, f)
        if not os.path.exists(filepath):
            missing.append(f)
    return missing


def load_gdf_if_exists(filepath: str):
    import geopandas as gpd
    if os.path.exists(filepath):
        return gpd.read_file(filepath)
    else:
        logging.warning(f"Файл {filepath} не найден. Переменной присвоено значение None.")
        return None


BC_TAGS = {
    'roads': {
        "highway": ["construction", "crossing", "living_street", "motorway", "motorway_link",
                    "motorway_junction", "pedestrian", "primary", "primary_link", "raceway",
                    "residential", "road", "secondary", "secondary_link", "services",
                    "tertiary", "tertiary_link", "track", "trunk", "trunk_link",
                    "turning_circle", "turning_loop", "unclassified"],
        "service": ["living_street", "emergency_access"]
    },
    'railways': {"railway": "rail"},
    'water': {
        'riverbank': True, 'reservoir': True, 'basin': True, 'dock': True,
        'canal': True, 'pond': True, 'natural': ['water', 'bay'],
        'waterway': ['river', 'canal', 'ditch'], 'landuse': 'basin', 'water': 'lake'
    }
}


def filter_gdf(gdf, rules, geom_types):
    import geopandas as gpd
    if gdf is None or gdf.empty:
        return None
    mask = gdf.geom_type.isin(geom_types)
    gdf = gdf[mask].copy()
    cols_to_check = []
    for col, rule in rules.items():
        if col in gdf.columns:
            cols_to_check.append(col)
            if isinstance(rule, list):
                gdf[col] = gdf[col].where(gdf[col].isin(rule))
            elif isinstance(rule, bool) and rule is True:
                gdf[col] = gdf[col].where(gdf[col].notna())
            else:
                gdf[col] = gdf[col].where(gdf[col] == rule)
    if cols_to_check:
        gdf = gdf.dropna(subset=cols_to_check, how='all').copy()
        gdf = gdf.dropna(axis=1, how='all')
    return gdf


def run_pipeline(data_dir: str, city_name: str, output_path: str):
    import geopandas as gpd
    import pandas as pd
    from blocksnet.blocks.cutting import preprocess_urban_objects, cut_urban_blocks
    from blocksnet.blocks.postprocessing import postprocess_urban_blocks
    from blocksnet.blocks.assignment import assign_land_use
    from blocksnet.blocks.aggregation import aggregate_objects
    from blocksnet.preprocessing.imputing import impute_buildings, impute_services
    from blocksnet.enums import LandUse

    data_dir = os.path.abspath(data_dir)
    data_dir_posix = data_dir.replace(os.sep, '/')
    
    missing = validate_inputs(data_dir)
    if missing:
        logging.error(f"Отсутствуют обязательные файлы: {missing}")
        return False, None
    
    logging.info("=== Этап 1: Загрузка данных ===")
    import osmnx as ox
    boundaries_gdf = ox.geocode_to_gdf(city_name)
    logging.info(f"Границы города загружены: {len(boundaries_gdf)} записей")

    roads_gdf = load_gdf_if_exists(f"{data_dir_posix}/roads.geojson")
    water_gdf = load_gdf_if_exists(f"{data_dir_posix}/water.geojson")
    railways_gdf = load_gdf_if_exists(f"{data_dir_posix}/railways.geojson")

    logging.info("=== Этап 2: Подготовка CRS ===")
    local_crs = boundaries_gdf.estimate_utm_crs()
    logging.info(f"Локальный CRS: {local_crs}")
    for gdf in [boundaries_gdf, roads_gdf, water_gdf]:
        if gdf is not None:
            gdf.to_crs(local_crs, inplace=True)
            gdf.reset_index(drop=True, inplace=True)

    logging.info("=== Этап 3: Фильтрация геометрий ===")
    roads_gdf = filter_gdf(roads_gdf, BC_TAGS['roads'], ['LineString', 'MultiLineString'])
    railways_gdf = filter_gdf(railways_gdf, BC_TAGS['railways'], ['LineString', 'MultiLineString'])
    water_gdf = filter_gdf(water_gdf, BC_TAGS['water'], ['Polygon'])

    logging.info("=== Этап 4: Генерация кварталов ===")
    lines_gdf, polygons_gdf = preprocess_urban_objects(
        roads_gdf=roads_gdf, railways_gdf=railways_gdf, water_gdf=water_gdf
    )
    blocks_gdf = cut_urban_blocks(boundaries_gdf, lines_gdf, polygons_gdf)
    blocks_gdf = postprocess_urban_blocks(blocks_gdf)
    logging.info(f"Сгенерировано кварталов: {len(blocks_gdf)}")

    logging.info("=== Этап 5: Функциональные зоны ===")
    functional_zones_gdf = gpd.read_file(f"{data_dir_posix}/terzones.geojson")
    functional_zones_gdf = functional_zones_gdf[['full_name', 'geometry']]
    functional_zones_gdf.to_crs(local_crs, inplace=True)
    functional_zones_gdf = functional_zones_gdf.rename(columns={'full_name': 'functional_zone'})
    functional_zones_gdf = functional_zones_gdf.reset_index(drop=True)

    blocks_gdf = blocks_gdf[['geometry']].reset_index(drop=True)

    rules_path = f"{data_dir_posix}/RULES_LU.json"
    with open(rules_path, 'r', encoding='utf-8') as f:
        raw_rules = json.load(f)
    RULES_LU = {key: getattr(LandUse, value) for key, value in raw_rules.items()}

    land_use_gdf = assign_land_use(blocks_gdf, functional_zones_gdf, RULES_LU)
    logging.info(f"Функциональные зоны назначены: {len(land_use_gdf)} записей")

    logging.info("=== Этап 6: Агрегация зданий ===")
    buildings_gdf = gpd.read_file(f"{data_dir_posix}/buildings.gpkg")
    buildings_gdf = buildings_gdf[buildings_gdf.geom_type.isin(['Polygon', 'MultiPolygon'])].copy()
    buildings_gdf.to_crs(local_crs, inplace=True)
    buildings_gdf = buildings_gdf.reset_index(drop=True)
    imp_gdf = impute_buildings(buildings_gdf, default_living_demand=20)
    agg_gdf, bad_gdf = aggregate_objects(blocks_gdf, buildings_gdf)
    agg_buildings_gdf = agg_gdf.join(land_use_gdf.drop(columns=['geometry']))
    logging.info(f"Здания агрегированы: {len(agg_buildings_gdf)} записей")

    logging.info("=== Этап 7: Агрегация сервисов ===")
    service_dir = f"{data_dir_posix}/platform"
    if os.path.exists(service_dir):
        blocks_gdf = agg_buildings_gdf.copy()
        for filename in os.listdir(service_dir):
            if not filename.endswith('.geojson'):
                continue
            service_name = os.path.splitext(filename)[0]
            filepath = os.path.join(service_dir, filename)
            try:
                gdf_raw = gpd.read_file(filepath).to_crs(local_crs)
                gdf_raw = gdf_raw[gdf_raw.geometry.notna() & ~gdf_raw.geometry.is_empty]
                if gdf_raw.empty:
                    logging.warning(f"  {service_name}: файл пуст, пропущен")
                    continue
                try:
                    gdf_raw = impute_services(gdf_raw, service_name)
                except Exception:
                    logging.info(f"  {service_name}: тип не найден в конфиге blocksnet")
                    if 'capacity' not in gdf_raw.columns:
                        gdf_raw['capacity'] = 0
                aggregated_gdf, _ = aggregate_objects(agg_buildings_gdf, gdf_raw)
                gdf_out = aggregated_gdf.drop(columns=['geometry']).rename(
                    columns={c: f'{c}_{service_name}' for c in aggregated_gdf.columns if c != 'geometry'}
                )
                blocks_gdf = blocks_gdf.join(gdf_out)
                logging.info(f"  {service_name}: OK")
            except Exception as e:
                logging.warning(f"  {service_name}: ошибка — {e}")
    else:
        logging.warning(f"Директория сервисов не найдена: {service_dir}")
        blocks_gdf = agg_buildings_gdf.copy()

    logging.info("=== Этап 8: Сохранение ===")
    blocks_gdf.to_file(output_path, driver='GPKG')
    logging.info(f"Результат сохранён: {output_path}")
    
    service_cols = [c for c in blocks_gdf.columns if c.startswith('count_')]
    logging.info(f"=== ИТОГ ===")
    logging.info(f"  Кварталов: {len(blocks_gdf)}")
    logging.info(f"  Здания (aggregated): {blocks_gdf['count'].sum() if 'count' in blocks_gdf.columns else 'N/A'}")
    logging.info(f"  Сервисов: {len(service_cols)} типов")
    return True, output_path


def main():
    parser = argparse.ArgumentParser(description="City blocks aggregation pipeline")
    parser.add_argument("--data-dir", default="data", help="Папка с входными данными (roads, water, buildings, terzones, RULES_LU.json, platform/)")
    parser.add_argument("--city", default="Урай", help="Название города для osmnx")
    parser.add_argument("--output", default="data/blocks.gpkg", help="Выходной файл blocks.gpkg")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    output_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    ok, result = run_pipeline(
        data_dir=args.data_dir,
        city_name=args.city,
        output_path=output_path
    )

    if ok:
        print(result)
        sys.exit(0)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
