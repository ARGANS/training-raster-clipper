"""
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

"""
Types 
"""
Mapping = Dict[str, int]  # Maps a feature class name to an integer.
ClassifiedSamples = Sequence[Sequence[float]]  # Rows of (*bands, class)
PolygonMask = npt.NDArray[np.uint8]  # Sparse 2D-matrix containing classes from polygons


class Color(Enum):
    RED = "B04"
    GREEN = "B03"
    BLUE = "B02"
    NIR = "B8A"


class TutorialStep(Enum):
    LOAD_SENTINEL_DATA = 100
    LOAD_FEATURE_POLYGONS = 200
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

    # Execute code until the desired tutorial step - if not provided, execute all as defined in the argumenty parser.
    try:
        tutorial_step = TutorialStep[args.tutorial_step]
    except KeyError:
        raise KeyError(
            f"Please choose one step among {list(e.name for e in TutorialStep)}"
        )

    info(args)

    # --

    interrupt_if_step_reached(tutorial_step, TutorialStep.LOAD_SENTINEL_DATA)
    rasters = load_sentinel_data(raster_input_path)
    if verbose:
        info(rasters)

    # --

    interrupt_if_step_reached(tutorial_step, TutorialStep.LOAD_FEATURE_POLYGONS)
    polygons = load_feature_polygons(polygons_input_path)
    if verbose:
        info(polygons)

    # --

    interrupt_if_step_reached(tutorial_step, TutorialStep.RASTERIZE_GEOJSON)
    burnt_polygons, mapping = rasterize_geojson(rasters, polygons)
    if verbose:
        info(burnt_polygons)
        info(mapping)

    # --

    interrupt_if_step_reached(tutorial_step, TutorialStep.PRODUCE_CLIPS)
    classified_rgb_rows = produce_clips(rasters, burnt_polygons, mapping)
    if verbose:
        info(classified_rgb_rows)

    # --

    interrupt_if_step_reached(tutorial_step, TutorialStep.PERSIST_TO_CSV)
    persist_to_csv(classified_rgb_rows, csv_output_path)
    info(f"Written CSV output {csv_output_path}")

    # --

    interrupt_if_step_reached(tutorial_step, TutorialStep.CLASSIFY_SENTINEL_DATA)
    classification_result = classify_sentinel_data(rasters, classified_rgb_rows)
    if verbose:
        info(classification_result)

    # --

    interrupt_if_step_reached(
        tutorial_step, TutorialStep.PERSIST_CLASSIFICATION_TO_RASTER
    )
    persist_classification_to_raster(raster_output_path, rasters, classification_result)
    info(f"Written Classified Raster to {csv_output_path}")

    # --

    info("Congratulations, you reached the end of the tutorial!")


def interrupt_if_step_reached(
    tutorial_step: TutorialStep, max_tutorial_step: TutorialStep
):
    if tutorial_step.value < max_tutorial_step.value:
        exit(f"Exit after step {tutorial_step}")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--raster_input_path", type=str, help="RGB raster")
    parser.add_argument(
        "-p", "--polygons_input_path", type=str, help="Classified polygons"
    )
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
        help="Execute code until the specified step",
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
    return parser


def parse_arguments(argument_parser: argparse.ArgumentParser):
    args = argument_parser.parse_args()

    assert args.raster_input_path, "Missing argument: raster_input_path"
    assert args.polygons_input_path, "Missing argument: polygons_input_path"
    assert args.csv_output_path, "Missing argument: csv_output_path"

    return args


def load_sentinel_data(
    sentinel_product_location: Path,
    *,
    resolution: Optional[Literal[60] | Literal[20] | Literal[10]] = 60,
) -> xr.DataArray:
    """Loads sentinel product

    Example input path: `S2A_MSIL2A_20221116T105321_N0400_R051_T31TCJ_20221116T170958.SAFE`

    Args:
        sentinel_product_location (Path): Location of the .SAFE folder containing a Sentinel-2 product.

    Returns:
        xr.DataArray: A DataArray containing the 3 RGB bands from the visible spectrum
    """

    pass  # TODO


def load_feature_polygons(input_path: Path) -> GeoDataFrame:

    pass  # TODO


def rasterize_geojson(
    data_array: xr.DataArray,
    training_classes: GeoDataFrame,
) -> Tuple[PolygonMask, Mapping]:
    """Burns a set of vectorial polygons to a raster.

    See https://gis.stackexchange.com/questions/316626/rasterio-features-rasterize

    Args:
        data_array (xr.DataArray): The Sentinel raster, from which data is taken, such as the transform or the shape.
        training_classes (GeoDataFrame): The input set of classified multipolygons to burn

    Returns:
        xr.DataArray: A mask raster generated from the polygons, representing the same geographical region as the source dataarray param
                      0 where no polygon were found, and integers representing classes in order of occurence in the GeoDataFrame
    """

    pass  # TODO


def produce_clips(
    data_array: xr.DataArray, burnt_polygons: PolygonMask, mapping: Mapping
) -> ClassifiedSamples:
    """Extract RGB values covered by classified polygons

    Args:
        data_array (xr.DataArray): RGB raster
        burnt_polygons (PolygonMask): Rasterized classified multipolygons

    Returns:
        _type_: A list of the RGB values contained in the data_array and their corresponding classes
    """

    pass  # TODO


def persist_to_csv(
    classified_rgb_rows: ClassifiedSamples,
    csv_output_path: Path,
) -> None:

    pass  # TODO


def classify_sentinel_data(
    rasters: xr.DataArray, classified_rgb_rows: ClassifiedSamples
) -> np.ndarray:

    pass  # TODO


def persist_classification_to_raster(
    raster_output_path: Path, rasters: xr.DataArray, classification_result: np.ndarray
) -> None:

    pass  # TODO


def info(object):
    logging.info(pformat(object))


def show(xds):
    ax = xds.plot.imshow(vmax=np.percentile(xds, 99.5))
    ax.axes.set_aspect("equal")


if __name__ == "__main__":
    main()
