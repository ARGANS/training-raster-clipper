"""
The goal of this utility is to create a CSV of (R, G, B, Class) from RGB rasters and classified polygons
It takes two inputs: 
- A path to a .SAFE file, eg the product downloaded directly from https://scihub.copernicus.eu/dhus/#/home
- A path to the classified polygons, in GeoJSON format?. Classes for now will be "binary", land and water.

It produces a CSV of R,G,B,Class columns. Only the data present in the polygons remains in the CSV, the rest is cut off.


TODO
Use the 60m lower resolution for faster iterations
Use RGB rasters (find band naming convention) in `S2A_MSIL2A_20221116T105321_N0400_R051_T31TCJ_20221116T170958S.SAFE` 


"""
from affine import Affine
import argparse
from pathlib import Path
from typing import (
    Optional,
    Literal,
    Sequence,
    Sequence,
)

import geopandas as gpd
import pandas as pd
import rasterio
import rioxarray
import xarray as xr
from pprint import pformat
import logging
import numpy as np

from enum import Enum

import matplotlib.pyplot as plt


class Color(Enum):
    RED = "B04"
    GREEN = "B03"
    BLUE = "B02"


class FeatureClass(Enum):
    WATER = 1
    FOREST = 2
    FARM = 3


def main():
    logging.basicConfig(level=logging.INFO)

    args = parse_arguments(build_argument_parser())

    raster_input_path = Path(args.raster_input_path)
    polygons_input_path = Path(args.polygons_input_path)
    csv_output_path = Path(args.csv_output_path)
    verbose = args.verbose

    if verbose:
        info(args)
        info(raster_input_path)
        info(polygons_input_path)
        info(csv_output_path)

    rasters = load_sentinel_data(raster_input_path)
    polygons = load_feature_polygons(polygons_input_path)
    classified_rgb_rows = produce_clips(rasters, rasterize_geojson(rasters, polygons))

    if verbose:
        info(rasters)
        info(polygons)
        info(classified_rgb_rows)

    persist_to_csv(classified_rgb_rows, csv_output_path)

    info(f"Written CSV output file to {csv_output_path}")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--raster_input_path", type=str, help="RGB raster")
    parser.add_argument(
        "-p", "--polygons_input_path", type=str, help="Classified polygons"
    )
    parser.add_argument("-o", "--csv_output_path", type=str, help="Output directory")
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

    # Assumes that the glob will return only one subfolder
    band_file_paths = {
        color: list(
            sentinel_product_location.glob(
                f"GRANULE/*/IMG_DATA/R{resolution}m/*_{color.value}_*"
            )
        )[0]
        for color in Color
    }

    bands: Sequence[xr.DataArray] = list(
        rioxarray.open_rasterio(band_file_paths[color])
        .astype(float)
        .assign_coords(coords={"band": [color.value]})
        for color in [Color.RED, Color.GREEN, Color.BLUE]
    )

    xds: xr.DataArray = xr.concat(bands, "band")

    # Normalization to a [0, 1] float, as Sentinel reflectances value are given in the [[0, 10000]] range
    return xds / 10000.0


def load_feature_polygons(input_path: Path) -> gpd.GeoDataFrame:
    return gpd.read_file(input_path).to_crs("32631")


def produce_clips(
    data_array: xr.DataArray, burnt_polygons: np.ndarray
) -> Sequence[Sequence[float]]:
    """Extract RGB values covered by classified polygons

    Args:
        data_array (xr.DataArray): RGB raster
        burnt_polygons (np.ndarray): Rasterized classified multipolygons

    Returns:
        _type_: A list of the RGB values contained in the data_array and their corresponding classes
    """

    xds = data_array

    feature_class_to_rgb_values = {
        c: xds.values[:, burnt_polygons == c.value].T for c in FeatureClass
    }

    # Refining: get a list of (R, G, B, feature class key) values
    return np.concatenate(
        [
            np.c_[values, np.ones(len(values)) * feature_class.value]
            for feature_class, values in feature_class_to_rgb_values.items()
        ]
    )


def rasterize_geojson(
    data_array: xr.DataArray,
    training_classes: gpd.GeoDataFrame,
) -> np.ndarray:
    """Burns a set of vectorial polygons to a raster.

    See https://gis.stackexchange.com/questions/316626/rasterio-features-rasterize

    Args:
        data_array (xr.DataArray): The Sentinel raster, from which data is taken, such as the transform or the shape.
        training_classes (gpd.GeoDataFrame): The input set of classified multipolygons to burn

    Returns:
        xr.DataArray: A mask raster generated from the polygons, representing the same geographical region as the source dataarray param
    """

    xds = data_array
    gdf = training_classes

    raster_transform = list(float(k) for k in xds.spatial_ref.GeoTransform.split())
    raster_transform = Affine.from_gdal(*raster_transform)

    # Remove the first value (band) and keep the dimensional ones
    out_shape = xds.shape[1:]

    # Extract couples of geometry and class required to rasterize
    shapes = [(row.geometry, row.class_key) for _, row in gdf.iterrows()]

    # ndarray means n-dimensional array
    burnt_polygons: np.ndarray = rasterio.features.rasterize(
        shapes,
        out_shape=out_shape,
        fill=0,
        transform=raster_transform,
        dtype=np.uint8,
    )

    # plt.imshow(burnt_polygons)
    # plt.show()

    return burnt_polygons


def persist_to_csv(
    classified_rgb_rows: Sequence[
        Sequence[
            float,
        ]
    ],
    csv_output_path: Path,
) -> None:
    df = pd.DataFrame(
        classified_rgb_rows, columns=[*(color.value for color in Color), "feature_key"]
    )
    df.to_csv(csv_output_path, index=False, sep=";")


def info(object):
    logging.info(pformat(object))


def show(xds):
    ax = xds.plot.imshow(vmax=np.percentile(xds, 99.5))
    ax.axes.set_aspect("equal")


if __name__ == "__main__":
    main()
