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

import argparse
import datetime
from pathlib import Path
from typing import Dict, Iterable, List, NoReturn, Set, Tuple, Union, Optional, Literal

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import rasterio
import rioxarray
from rioxarray.merge import merge_arrays
import xarray as xr
import os
from pprint import pformat
import logging

from enum import Enum

class Color(Enum):
    RED = 2
    GREEN = 3
    BLUE = 4

def main():
    logging.basicConfig(level=logging.DEBUG)

    args = parse_arguments()
    logging.info(args)

    raster_input_path = Path(args.raster_input_path)
    polygons_input_path = Path(args.polygons_input_path)
    csv_output_path = Path(args.csv_output_path)

    rasters = read_sentinel_data(raster_input_path)
    polygons = read_polygons(polygons_input_path)

    produce_clips(rasters, polygons, csv_output_path)

    logging.debug(raster_input_path)
    logging.debug(polygons_input_path)
    logging.debug(csv_output_path)


def parse_arguments():
    argparser = build_argument_parser()
    args = argparser.parse_args()

    assert args.raster_input_path, "Missing argument: raster_input_path"
    assert args.polygons_input_path, "Missing argument: polygons_input_path"
    assert args.csv_output_path, "Missing argument: csv_output_path"
    
    return args


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--raster_input_path", type=str, help="RGB raster")
    parser.add_argument(
        "-p", "--polygons_input_path", type=str, help="Classified polygons"
    )
    parser.add_argument("-o", "--csv_output_path", type=str, help="Output directory")
    return parser


"""
Example input path: `S2A_MSIL2A_20221116T105321_N0400_R051_T31TCJ_20221116T170958.SAFE`

S2A_MSIL2A_20221116T105321_N0400_R051_T31TCJ_20221116T170958.
L2A_T31TCJ_A038658_20221116T105603
"""


def read_sentinel_data(
    sentinel_product_location: Path, 
    *, 
    resolution: Optional[Literal[60] | Literal[20] | Literal[10]] = 60
) -> xr.Dataset:
    """Loads sentinel product

    Args:
        sentinel_product_location (Path): Location of the .SAFE folder containing a Sentinel-2 product.

    Returns:
        xr.Dataset: A dataset containing the 3 RGB bands from the visible spectrum
    """

    granule_path = sentinel_product_location / 'GRANULE'

    granule_subfolders = os.listdir(granule_path)

    # TODO eschalk: Can it contains 0 or 1+ elements? Default: use the first one 
    assert len(granule_subfolders) == 1, "Expected exactly one subfolder in GRANULE"

    granule_subfolder = Path(granule_subfolders[0]) 

    resolution_path = granule_path / granule_subfolder / 'IMG_DATA' / f'R{resolution}m'

    resolution_subfolders = set(os.listdir(resolution_path))

    band_file_paths = {
        color_enum: resolution_path / next(iter({x for x in resolution_subfolders if f'_B0{color_enum.value}_' in x}))
        for color_enum in Color
    }

    
# ds = xr.open_rasterio('D:\Profils\eschalk\Downloads\S2A_MSIL2A_20221116T105321_N0400_R051_T31TCJ_20221116T170958\S2A_MSIL2A_20221116T105321_N0400_R051_T31TCJ_20221116T170958.SAFE\GRANULE\L2A_T31TCJ_A038658_20221116T105603\IMG_DATA\R10m\T31TCJ_20221116T105321_TCI_10m.jp2')
    
    logging.debug(pformat(band_file_paths))



    # xds = rioxarray.open_rasterio(band_file_paths[Color.RED])
    xds = merge_arrays([
        rioxarray.open_rasterio(band_file_paths[Color.RED]),
        rioxarray.open_rasterio(band_file_paths[Color.GREEN]),
        rioxarray.open_rasterio(band_file_paths[Color.BLUE]),
    ])

    logging.debug(pformat(xds))

    ax = xds.plot.imshow()
    ax.axes.set_aspect('equal')
    plt.show()

    return None  # TODO eschalk


def read_polygons(input: Path) -> gpd.GeoDataFrame:

    return None  # TODO eschalk


def produce_clips(
    dataset: xr.Dataset,
    training_classes: gpd.GeoDataFrame,
    output: Path,
) -> None:

    pass


if __name__ == "__main__":
    main()
