from training_raster_clipper.core.models import TrainingConfiguration, TrainingFunctions
from training_raster_clipper.core.logging import log_info

from training_raster_clipper.core.visualization import (
    plot_rgb_data_array,
    plot_array,
    plot_geodataframe,
)

import matplotlib.pyplot as plt


def execute_catch(config: TrainingConfiguration, interface: TrainingFunctions) -> None:
    try:
        execute(config, interface)
    except NotImplementedError:
        log_info("Function is not implemented, stopping execution now.")
        plt.show(block=True)
    finally:
        plt.show(block=True)


def execute(config: TrainingConfiguration, interface: TrainingFunctions) -> None:
    log_info(f"Execute implementation '{config.implementation_name}' with params:")
    log_info(f"{config = }")
    log_info(f"{interface = }")

    verbose = config.verbose
    show_plots = config.show_plots

    resolution = config.resolution
    band_names = config.band_names

    raster_input_path = config.raster_input_path
    polygons_input_path = config.polygons_input_path
    csv_output_path = config.csv_output_path
    raster_output_path = config.raster_output_path

    polygons = interface.load_feature_polygons(polygons_input_path)
    if verbose:
        log_info(polygons, "polygons")
    if show_plots:
        plot_geodataframe(polygons, f"{interface.load_feature_polygons.__name__}")

    # --

    rasters = interface.load_sentinel_data(raster_input_path, resolution, band_names)
    if verbose:
        log_info(rasters, "rasters")
    if show_plots:
        plot_rgb_data_array(rasters, f"{interface.load_sentinel_data.__name__}")

    # --

    burnt_polygons, mapping = interface.rasterize_geojson(rasters, polygons)
    if verbose:
        log_info(burnt_polygons, "burnt_polygons")
        log_info(mapping, "mapping")
    if show_plots:
        plot_array(burnt_polygons, f"{interface.rasterize_geojson.__name__}")

    # --

    classified_rgb_rows = interface.produce_clips(rasters, burnt_polygons, mapping)
    if verbose:
        log_info(classified_rgb_rows, "classified_rgb_rows")

    # --

    interface.persist_to_csv(classified_rgb_rows, csv_output_path)
    log_info(f"Written CSV output {csv_output_path}")

    # --

    classification_result = interface.classify_sentinel_data(
        rasters, classified_rgb_rows
    )
    if verbose:
        log_info(classification_result, "classification_result")
    if show_plots:
        plot_array(
            classification_result, f"{interface.classify_sentinel_data.__name__}"
        )

    # --

    interface.persist_classification_to_raster(
        raster_output_path, classification_result
    )
    log_info(f"Written Classified Raster to {csv_output_path}")

    # --

    log_info("Congratulations, you reached the end of the tutorial!")
