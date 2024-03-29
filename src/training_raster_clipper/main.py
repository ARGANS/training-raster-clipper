"""
--------------------------------------------------------------------------------------------------------
TUTORIAL-READER: YOU DO NOT NEED TO MODIFY THIS FILE, ONLY `implementation/your_work.py`!
--------------------------------------------------------------------------------------------------------

The goal of this utility is to create a CSV of (R, G, B, Class) from RGB rasters and classified polygons
It takes two inputs: 
- A path to a .SAFE file, eg the product downloaded directly from https://scihub.copernicus.eu/dhus/#/home
- A path to the classified polygons, in GeoJSON format?. Classes for now will be "binary", land and water.

It produces a CSV of R,G,B,Class columns. Only the data present in the polygons remains in the CSV, the rest is cut off.


Use the 60m lower resolution for faster iterations
Use RGB rasters (find band naming convention) in `S2A_MSIL2A_20221116T105321_N0400_R051_T31TCJ_20221116T170958S.SAFE` 
"""

import argparse
from enum import Enum
from pathlib import Path

import matplotlib.pyplot as plt

from training_raster_clipper.implementation import eschalk, iatraoui, rskandrani, nbertaud
from training_raster_clipper.core.visualization import (
    plot_rgb_data_array,
    plot_array,
    plot_geodataframe,
)
from training_raster_clipper.core.logging import log_info
import logging

CHEAT_MODE_IMPLEMENTATION = "eschalk"


class TutorialStep(Enum):
    NONE = 0
    LOAD_FEATURE_POLYGONS = 100
    LOAD_SENTINEL_DATA = 200
    RASTERIZE_GEOJSON = 300
    PRODUCE_CLIPS = 400
    PERSIST_TO_CSV = 500
    CLASSIFY_SENTINEL_DATA = 600
    PERSIST_CLASSIFICATION_TO_RASTER = 700
    END = 9999999


def main():
    logging.basicConfig(level=logging.INFO)

    args = parse_arguments(build_argument_parser())

    verbose = args.verbose
    show_plots = args.figures

    raster_input_path = Path(args.raster_input_path)
    polygons_input_path = Path(args.polygons_input_path)
    csv_output_path = Path(args.csv_output_path)
    raster_output_path = Path(args.raster_output_path)
    implementation = args.implementation

    implementations = {
        "eschalk": eschalk,
        "iatraoui": iatraoui,
        "rskandrani": rskandrani,
        "nbertaud": nbertaud
    }
    assert implementation in implementations

    interface = (
        implementations[CHEAT_MODE_IMPLEMENTATION]
        if args.cheat
        else implementations[implementation]
    )

    # Execute code until the desired tutorial step - if not provided, execute all as defined in the argumenty parser.
    try:
        tutorial_step = TutorialStep[args.tutorial_step]
    except KeyError:
        raise KeyError(
            f"Please choose one step among {list(e.name for e in TutorialStep)}"
        )

    log_info(args)

    resolution = 60
    band_names = ("B04", "B03", "B02", "B8A")

    # --

    current_step = TutorialStep.LOAD_FEATURE_POLYGONS
    interrupt_if_step_reached(tutorial_step, current_step)
    polygons = interface.load_feature_polygons(polygons_input_path)
    if verbose:
        log_info(polygons, "polygons")
    if show_plots:
        plot_geodataframe(polygons, render_tutorial_step(current_step))

    # --

    current_step = TutorialStep.LOAD_SENTINEL_DATA
    interrupt_if_step_reached(tutorial_step, current_step)
    rasters = interface.load_sentinel_data(raster_input_path, resolution, band_names)
    if verbose:
        log_info(rasters, "rasters")
    if show_plots:
        plot_rgb_data_array(rasters, render_tutorial_step(current_step))

    # --

    current_step = TutorialStep.RASTERIZE_GEOJSON
    interrupt_if_step_reached(tutorial_step, current_step)
    burnt_polygons, mapping = interface.rasterize_geojson(rasters, polygons)
    if verbose:
        log_info(burnt_polygons, "burnt_polygons")
        log_info(mapping, "mapping")
    if show_plots:
        plot_array(burnt_polygons, render_tutorial_step(current_step))

    # --

    current_step = TutorialStep.PRODUCE_CLIPS
    interrupt_if_step_reached(tutorial_step, current_step)
    classified_rgb_rows = interface.produce_clips(rasters, burnt_polygons, mapping)
    if verbose:
        log_info(classified_rgb_rows, "classified_rgb_rows")

    # --

    current_step = TutorialStep.PERSIST_TO_CSV
    interrupt_if_step_reached(tutorial_step, current_step)
    interface.persist_to_csv(classified_rgb_rows, csv_output_path)
    log_info(f"Written CSV output {csv_output_path}")

    # --

    current_step = TutorialStep.CLASSIFY_SENTINEL_DATA
    interrupt_if_step_reached(tutorial_step, current_step)
    classification_result = interface.classify_sentinel_data(
        rasters, classified_rgb_rows
    )
    if verbose:
        log_info(classification_result, "classification_result")
    if show_plots:
        plot_array(classification_result, render_tutorial_step(current_step))

    # --

    current_step = TutorialStep.PERSIST_CLASSIFICATION_TO_RASTER
    interrupt_if_step_reached(tutorial_step, current_step)
    interface.persist_classification_to_raster(
        raster_output_path, classification_result
    )
    log_info(f"Written Classified Raster to {csv_output_path}")

    # --

    log_info("Congratulations, you reached the end of the tutorial!")

    current_step = TutorialStep.END
    interrupt_if_step_reached(tutorial_step, current_step)


def render_tutorial_step(current_step):
    return f"({int(current_step.value/100)}: {current_step.name})"


def interrupt_if_step_reached(
    tutorial_step: TutorialStep, max_tutorial_step: TutorialStep
):
    if (tutorial_step.value < max_tutorial_step.value) or (
        max_tutorial_step == TutorialStep.END
    ):
        plt.show(block=True)
        log_info(f"Exit after step {tutorial_step}")
        exit()
    else:
        log_info(f"Executing step: {max_tutorial_step}")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--implementation",
        type=str,
        help="Python Module Name containing the implementation of the training to run",
    )
    parser.add_argument(
        "-p", "--polygons_input_path", type=str, help="Classified polygons"
    )
    parser.add_argument("-r", "--raster_input_path", type=str, help="RGB raster")
    parser.add_argument(
        "-o",
        "--csv_output_path",
        type=str,
        help="Output path for CSV classified points",
    )
    parser.add_argument(
        "-s",
        "--raster_output_path",
        type=str,
        help="Output path for the raster resulting from sklearn",
    )
    parser.add_argument(
        "-t",
        "--tutorial_step",
        type=str,
        help=(
            "Execute code until the specified step. The step must be a value among"
            f" {list(e.name for e in TutorialStep)}. If not specified, run all steps."
        ),
        default=TutorialStep.END.name,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        type=bool,
        nargs="?",
        const=True,
        default=False,
        help="Verbose",
    )
    parser.add_argument(
        "-c",
        "--cheat",
        type=bool,
        nargs="?",
        const=True,
        default=False,
        help=(
            "Cheating: you can switch between the solution file or your own work, as"
            " they define the same functions."
        ),
    )
    parser.add_argument(
        "-f",
        "--figures",
        type=bool,
        nargs="?",
        const=True,
        default=False,
        help="Show figures at the end of the script execution. By default True",
    )
    return parser


def parse_arguments(argument_parser: argparse.ArgumentParser):
    args = argument_parser.parse_args()

    assert args.raster_input_path, "Missing argument: raster_input_path"
    assert args.polygons_input_path, "Missing argument: polygons_input_path"
    assert args.csv_output_path, "Missing argument: csv_output_path"
    assert args.raster_output_path, "Missing argument: raster_output_path"

    if not args.cheat:
        assert args.implementation

    return args


if __name__ == "__main__":
    main()
