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
from typing import Dict, Iterable, List, NoReturn, Set, Tuple, Union

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import rasterio
import rioxarray
import xarray as xr
import os


def main():
    args = parse_arguments()
    print(args)

    raster_input_path = Path(args.raster_input_path)
    polygons_input_path = Path(args.polygons_input_path)
    csv_output_path = Path(args.csv_output_path)

    rasters = read_sentinel_data(raster_input_path)
    polygons = read_polygons(polygons_input_path)

    produce_clips(rasters, polygons, csv_output_path)

    print(raster_input_path)
    print(polygons_input_path)
    print(csv_output_path)


def parse_arguments():
    argparser = build_argument_parser()
    args = argparser.parse_args()
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


def read_sentinel_data(input: Path) -> xr.Dataset:
    granule_dir = input / 'GRANULE'
    granule_subfolder = os.listdir(granule_dir)[0] # TODO eschalk: Can it contains 0 or 1+ elements?
    # granule_subfolder = "L2A_T31TCJ_A038658_20221116T105603"  # TODO eschalk:
    img_data = granule_subfolder / 'IMG_DATA' 


    red_band_path =   "R60m"

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
