import logging
import argparse
import os
import sys


OUTPUT_FILENAMES = {
    "accessibility": "data/accessibility.gpkg",
    "connectivity": "data/connectivity.gpkg", 
    "area": "data/area_accessibility.gpkg",
    "network_analysis": "data/network_analysis.gpkg"
}


def check_blocks_exists(blocks_path: str) -> bool:
    if os.path.exists(blocks_path):
        logging.info(f"blocks.gpkg найден: {blocks_path}")
        return True
    else:
        logging.warning(f"blocks.gpkg НЕ найден: {blocks_path}")
        return False


def run_accessibility_metrics(blocks_path: str, acc_mx_path: str, output_path: str):
    import pandas as pd
    import geopandas as gpd
    from blocksnet.analysis.network.accessibility import (
        median_accessibility, mean_accessibility, max_accessibility
    )

    logging.info("Загрузка accessibility matrix")
    acc_mx = pd.read_pickle(acc_mx_path)
    logging.info(f"Matrix shape: {acc_mx.shape}")

    blocks = gpd.read_file(blocks_path)
    local_crs = blocks.estimate_utm_crs()
    blocks = blocks.to_crs(local_crs)

    logging.info("=== Median accessibility ===")
    med_acc = median_accessibility(acc_mx)
    med_acc.columns = ['median_accessibility']

    logging.info("=== Mean accessibility ===")
    mean_acc = mean_accessibility(acc_mx)
    mean_acc.columns = ['mean_accessibility']

    logging.info("=== Max accessibility ===")
    max_acc = max_accessibility(acc_mx)
    max_acc.columns = ['max_accessibility']

    metrics = pd.concat([med_acc, mean_acc, max_acc], axis=1)
    for col in metrics.columns:
        metrics[col] = metrics[col].astype('float32')
    result = blocks[['geometry']].join(metrics)
    result.to_file(output_path, driver='GPKG')
    logging.info(f"Сохранено: {output_path}")
    return True, output_path


def run_connectivity_metrics(blocks_path: str, acc_mx_path: str, output_path: str):
    import pandas as pd
    import geopandas as gpd
    from blocksnet.analysis.network.accessibility import mean_accessibility
    from blocksnet.analysis.network.connectivity import calculate_connectivity

    logging.info("Загрузка accessibility matrix")
    acc_mx = pd.read_pickle(acc_mx_path)

    blocks = gpd.read_file(blocks_path)
    local_crs = blocks.estimate_utm_crs()
    blocks = blocks.to_crs(local_crs)

    logging.info("=== Mean accessibility ===")
    mean_acc = mean_accessibility(acc_mx)
    mean_acc.columns = ['mean_accessibility']

    logging.info("=== Connectivity ===")
    connectivity = calculate_connectivity(mean_acc)

    result = blocks[['geometry']].join(connectivity)
    result.to_file(output_path, driver='GPKG')
    logging.info(f"Сохранено: {output_path}")
    return True, output_path


def run_area_accessibility(blocks_path: str, acc_mx_path: str, output_path: str):
    import pandas as pd
    import geopandas as gpd
    from blocksnet.analysis.network.accessibility import area_accessibility

    logging.info("Загрузка accessibility matrix")
    acc_mx = pd.read_pickle(acc_mx_path)

    blocks = gpd.read_file(blocks_path)
    local_crs = blocks.estimate_utm_crs()
    blocks = blocks.to_crs(local_crs)

    if 'site_area' not in blocks.columns:
        blocks['site_area'] = blocks.geometry.area
        logging.info("Добавлена колонка site_area")

    logging.info("=== Area accessibility ===")
    area_acc = area_accessibility(acc_mx, blocks)
    area_acc.columns = ['area_accessibility']

    result = blocks[['geometry']].join(area_acc)
    result.to_file(output_path, driver='GPKG')
    logging.info(f"Сохранено: {output_path}")
    return True, output_path


def run_network_analysis(blocks_path: str, acc_mx_path: str, output_path: str):
    import pandas as pd
    import geopandas as gpd
    from blocksnet.analysis.network.accessibility import (
        median_accessibility, mean_accessibility, max_accessibility, area_accessibility
    )
    from blocksnet.analysis.network.connectivity import calculate_connectivity

    logging.info("Загрузка accessibility matrix")
    acc_mx = pd.read_pickle(acc_mx_path)

    blocks = gpd.read_file(blocks_path)
    local_crs = blocks.estimate_utm_crs()
    blocks = blocks.to_crs(local_crs)

    if 'site_area' not in blocks.columns:
        blocks['site_area'] = blocks.geometry.area

    logging.info("=== Median accessibility ===")
    med_acc = median_accessibility(acc_mx)
    med_acc.columns = ['median_accessibility']

    logging.info("=== Mean accessibility ===")
    mean_acc = mean_accessibility(acc_mx)
    mean_acc.columns = ['mean_accessibility']

    logging.info("=== Max accessibility ===")
    max_acc = max_accessibility(acc_mx)
    max_acc.columns = ['max_accessibility']

    logging.info("=== Connectivity ===")
    connectivity = calculate_connectivity(mean_acc)

    logging.info("=== Area accessibility ===")
    area_acc = area_accessibility(acc_mx, blocks)
    area_acc.columns = ['area_accessibility']

    metrics = pd.concat([med_acc, mean_acc, max_acc, connectivity, area_acc], axis=1)
    for col in metrics.columns:
        metrics[col] = metrics[col].astype('float32')

    result = blocks[['geometry']].join(metrics)
    result.to_file(output_path, driver='GPKG')
    logging.info(f"Сохранено: {output_path}")
    return True, output_path


def main():
    parser = argparse.ArgumentParser(description="Transport metrics using blocksnet")
    parser.add_argument("--blocks", default="data/blocks.gpkg", help="Input blocks.gpkg")
    parser.add_argument("--acc-mx", default="data/acc_mx.pickle", help="Accessibility matrix pickle")
    parser.add_argument("--metric", required=True, 
                        choices=["accessibility", "connectivity", "area", "network_analysis"],
                        help="Metric to calculate")
    parser.add_argument("--output", default=None, help="Output path (auto-generated if not specified)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if not check_blocks_exists(args.blocks):
        logging.error("blocks.gpkg не найден. Сначала запусти city-blocks-aggregator")
        sys.exit(1)

    if not os.path.exists(args.acc_mx):
        logging.error(f"accessibility_matrix не найден: {args.acc_mx}")
        sys.exit(1)

    output_path = args.output
    if output_path is None:
        output_path = OUTPUT_FILENAMES.get(args.metric, "data/transport.gpkg")
    
    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    if args.metric == "accessibility":
        ok, result = run_accessibility_metrics(args.blocks, args.acc_mx, output_path)
    elif args.metric == "connectivity":
        ok, result = run_connectivity_metrics(args.blocks, args.acc_mx, output_path)
    elif args.metric == "area":
        ok, result = run_area_accessibility(args.blocks, args.acc_mx, output_path)
    elif args.metric == "network_analysis":
        ok, result = run_network_analysis(args.blocks, args.acc_mx, output_path)

    if ok:
        print(result)
        sys.exit(0)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
