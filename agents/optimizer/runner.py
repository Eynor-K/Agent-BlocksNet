import logging
import argparse
import os
import sys
import pandas as pd
import geopandas as gpd

def run_optimization(blocks_path: str, acc_mx_path: str, block_id: int, land_use: str = None, output_path: str = None, max_runs: int = 100, timeout: int = 300):
    try:
        from blocksnet.optimization.services import (
            TPEOptimizer, WeightedObjective, WeightedConstraints,
            Facade, AreaSolution, RandomOrder, GradientChooser
        )
        from blocksnet.config import service_types_config
        from blocksnet.enums import LandUse

        logging.info(f"Загрузка blocks: {blocks_path}")
        blocks = gpd.read_file(blocks_path)
        local_crs = blocks.estimate_utm_crs()
        blocks = blocks.to_crs(local_crs)

        if 'block_id' not in blocks.columns:
            blocks['block_id'] = range(len(blocks))

        logging.info(f"Загрузка accessibility matrix: {acc_mx_path}")
        acc_mx = pd.read_pickle(acc_mx_path)

        target_block = blocks[blocks['block_id'] == block_id]
        if target_block.empty:
            logging.error(f"Квартал с block_id={block_id} не найден")
            return False, f"block_id {block_id} not found"

        block_idx = target_block.index[0]

        # Определяем land use для целевого квартала
        current_land_use = target_block.iloc[0].get('land_use', None)
        target_land_use_str = land_use if land_use else current_land_use

        if not target_land_use_str:
            logging.error(f"Не указан land_use и он отсутствует в квартале")
            return False, "land_use is missing"

        # Пытаемся получить Enum
        try:
            target_land_use_enum = LandUse[target_land_use_str]
        except KeyError:
            try:
                target_land_use_enum = LandUse(target_land_use_str)
            except ValueError:
                logging.error(f"Неизвестный land_use: {target_land_use_str}")
                return False, f"Unknown land_use: {target_land_use_str}"

        logging.info(f"Оптимизация для квартала block_id={block_id}, новый land_use={target_land_use_enum.name}")

        # Подготавливаем словарь blocks_lu
        # В пайплайне нужно указывать только те кварталы, которые оптимизируются!
        # Либо все, но с корректными LandUse
        blocks_lu = {block_idx: target_land_use_enum}

        # Доступные сервисы по config
        available_services = service_types_config[target_land_use_enum]
        if not available_services:
            logging.warning(f"Для land_use={target_land_use_enum.name} нет доступных сервисов")
            available_services = list(service_types_config.values())[0][:5]

        logging.info(f"Будут оптимизированы сервисы: {available_services}")

        # Расчет площади
        blocks['site_area'] = blocks.to_crs(blocks.estimate_utm_crs()).area

        var_adapter = AreaSolution(blocks_lu)

        facade = Facade(
            blocks_lu=blocks_lu,
            blocks_df=blocks,
            accessibility_matrix=acc_mx,
            var_adapter=var_adapter,
        )

        service_weights = {service: 1.0 for service in available_services}

        for service_type in available_services:
            col_name = f'capacity_{service_type}'
            if col_name in blocks.columns:
                caps = blocks[[col_name]].fillna(0).rename(columns={col_name: 'capacity'})
            else:
                caps = pd.DataFrame({'capacity': [0.0] * len(blocks)}, index=blocks.index)
            facade.add_service_type(service_type, 1.0, caps)

        objective = WeightedObjective(num_params=facade.num_params, facade=facade, weights=service_weights, max_evals=max_runs)
        constraints = WeightedConstraints(num_params=facade.num_params, facade=facade, priority=service_weights)

        logging.info(f"Запуск TPE optimizer: max_runs={max_runs}, timeout={timeout}")
        tpe_optimizer = TPEOptimizer(
            objective=objective, 
            constraints=constraints, 
            vars_order=RandomOrder(), 
            vars_chooser=GradientChooser(facade, num_params=facade.num_params, num_top=5)
        )

        best_x, best_val, perc, func_evals = tpe_optimizer.run(max_runs=max_runs, timeout=timeout, initial_runs_num=1)

        logging.info(f"Optimization complete: best_val={best_val}, func_evals={func_evals}")

        solution_df = facade.solution_to_services_df(best_x)

        if output_path is None:
            output_path = f"data/optimization_block_{block_id}.gpkg"
        
        output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        
        # solution_df не имеет геометрии по умолчанию
        # Соединим с геометрией квартала
        target_geometry = target_block.geometry.values[0]
        solution_gdf = gpd.GeoDataFrame(solution_df, geometry=[target_geometry] * len(solution_df), crs=blocks.crs)

        solution_gdf.to_file(output_path, driver='GPKG')

        logging.info(f"Сохранено: {output_path}")
        return True, output_path

    except Exception as e:
        logging.error(f"Ошибка оптимизации: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="Block service optimization using TPE")
    parser.add_argument("--blocks", default="data/blocks.gpkg", help="Input blocks.gpkg")
    parser.add_argument("--acc-mx", default="data/acc_mx.pickle", help="Accessibility matrix")
    parser.add_argument("--block-id", type=int, required=True, help="Block ID to optimize")
    parser.add_argument("--land-use", type=str, default=None, help="New Land use type (e.g. RESIDENTIAL, BUSINESS)")
    parser.add_argument("--output", default=None, help="Output path")
    parser.add_argument("--max-runs", type=int, default=100, help="Max optimization runs")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if not os.path.exists(args.blocks):
        logging.error(f"blocks.gpkg не найден: {args.blocks}")
        sys.exit(1)

    if not os.path.exists(args.acc_mx):
        logging.error(f"acc_mx.pickle не найден: {args.acc_mx}")
        sys.exit(1)

    ok, result = run_optimization(
        blocks_path=args.blocks,
        acc_mx_path=args.acc_mx,
        block_id=args.block_id,
        land_use=args.land_use,
        output_path=args.output,
        max_runs=args.max_runs,
        timeout=args.timeout
    )

    if ok:
        print(f"Success: {result}")
        sys.exit(0)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()