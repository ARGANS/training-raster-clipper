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
import logging
from enum import Enum
from pathlib import Path
from pprint import pformat
from typing import Dict, Literal, Optional, Sequence, Tuple

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import pandas as pd
import rasterio
import rioxarray
import xarray as xr
from affine import Affine
from geopandas.geodataframe import GeoDataFrame
from sklearn.ensemble import RandomForestClassifier

from implementation import solutions
from implementation import your_work


class TutorialStep(Enum):
    NONE = 0
    LOAD_FEATURE_POLYGONS = 100
    LOAD_SENTINEL_DATA = 200
    RASTERIZE_GEOJSON = 300
    PRODUCE_CLIPS = 400
    PERSIST_TO_CSV = 500
    CLASSIFY_SENTINEL_DATA = 600
    PERSIST_CLASSIFICATION_TO_RASTER = 700
    ALL = 9999999


def main():
    logging.basicConfig(level=logging.INFO)

    args = parse_arguments(build_argument_parser())

    verbose = args.verbose

    raster_input_path = Path(args.raster_input_path)
    polygons_input_path = Path(args.polygons_input_path)
    csv_output_path = Path(args.csv_output_path)
    raster_output_path = Path(args.raster_output_path)

    interface = solutions if args.cheat else your_work

    # Execute code until the desired tutorial step - if not provided, execute all as defined in the argumenty parser.
    try:
        tutorial_step = TutorialStep[args.tutorial_step]
    except KeyError:
        raise KeyError(
            f"Please choose one step among {list(e.name for e in TutorialStep)}"
        )

    info(args)

    # --

    interrupt_if_step_reached(tutorial_step, TutorialStep.LOAD_FEATURE_POLYGONS)
    polygons = interface.load_feature_polygons(polygons_input_path)
    if verbose:
        info(polygons)

    # --

    interrupt_if_step_reached(tutorial_step, TutorialStep.LOAD_SENTINEL_DATA)
    rasters = interface.load_sentinel_data(raster_input_path)
    if verbose:
        info(rasters)

    # --

    interrupt_if_step_reached(tutorial_step, TutorialStep.RASTERIZE_GEOJSON)
    burnt_polygons, mapping = interface.rasterize_geojson(rasters, polygons)
    if verbose:
        info(burnt_polygons)
        info(mapping)

    # --

    interrupt_if_step_reached(tutorial_step, TutorialStep.PRODUCE_CLIPS)
    classified_rgb_rows = interface.produce_clips(rasters, burnt_polygons, mapping)
    if verbose:
        info(classified_rgb_rows)

    # --

    interrupt_if_step_reached(tutorial_step, TutorialStep.PERSIST_TO_CSV)
    interface.persist_to_csv(classified_rgb_rows, csv_output_path)
    info(f"Written CSV output {csv_output_path}")

    # --

    interrupt_if_step_reached(tutorial_step, TutorialStep.CLASSIFY_SENTINEL_DATA)
    classification_result = interface.classify_sentinel_data(
        rasters, classified_rgb_rows
    )
    if verbose:
        info(classification_result)

    # --

    interrupt_if_step_reached(
        tutorial_step, TutorialStep.PERSIST_CLASSIFICATION_TO_RASTER
    )
    interface.persist_classification_to_raster(
        raster_output_path, rasters, classification_result
    )
    info(f"Written Classified Raster to {csv_output_path}")

    # --

    info("Congratulations, you reached the end of the tutorial!")


def interrupt_if_step_reached(
    tutorial_step: TutorialStep, max_tutorial_step: TutorialStep
):
    if tutorial_step.value < max_tutorial_step.value:
        exit(f"Exit after step {tutorial_step}")
    info(f"Executing step: {max_tutorial_step}")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
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
        help=f"Execute code until the specified step. The step must be a value among {list(e.name for e in TutorialStep)}. If not specified, run all steps.",
        default=TutorialStep.ALL.name,
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
        help="Cheating: you can switch between the solution file or your own work, as they define the same functions.",
    )
    return parser


def parse_arguments(argument_parser: argparse.ArgumentParser):
    args = argument_parser.parse_args()

    assert args.raster_input_path, "Missing argument: raster_input_path"
    assert args.polygons_input_path, "Missing argument: polygons_input_path"
    assert args.csv_output_path, "Missing argument: csv_output_path"

    return args


def info(object):
    if type(object) == str:
        logging.info(object)
    else:
        logging.info(pformat(object))


def show(xds):
    ax = xds.plot.imshow(vmax=np.percentile(xds, 99.5))
    ax.axes.set_aspect("equal")


if __name__ == "__main__":
    main()
