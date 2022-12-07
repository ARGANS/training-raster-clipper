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
from typing import (
    Dict,
    Iterable,
    List,
    NoReturn,
    Set,
    Tuple,
    Union,
    Optional,
    Literal,
    Sequence,
)

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import rasterio
import rioxarray
import xarray as xr
from pprint import pformat
import logging
from rasterio.mask import mask
import numpy as np

from enum import Enum

config = {
    "plot": False,
}


class Color(Enum):
    RED = "B04"
    GREEN = "B03"
    BLUE = "B02"


def main():
    logging.basicConfig(level=logging.INFO)

    args = parse_arguments()
    logging.info(args)

    raster_input_path = Path(args.raster_input_path)
    polygons_input_path = Path(args.polygons_input_path)
    csv_output_path = Path(args.csv_output_path)

    rasters = read_sentinel_data(raster_input_path)
    polygons = read_polygons(polygons_input_path)

    produce_clips(rasters, polygons, csv_output_path)

    logging.info(raster_input_path)
    logging.info(polygons_input_path)
    logging.info(csv_output_path)


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
`
S2A_MSIL2A_20221116T105321_N0400_R051_T31TCJ_20221116T170958.
L2A_T31TCJ_A038658_20221116T105603
"""


def read_sentinel_data(
    sentinel_product_location: Path,
    *,
    resolution: Optional[Literal[60] | Literal[20] | Literal[10]] = 60,
) -> xr.DataArray:
    """Loads sentinel product

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

    logging.info(pformat(band_file_paths))

    bands: Sequence[xr.DataArray] = list(
        rioxarray.open_rasterio(band_file_paths[color])
        .astype(float)
        .assign_coords(coords={"band": [color.value]})
        for color in [Color.RED, Color.GREEN, Color.BLUE]
    )
    info("bands")
    info(bands)

    xds: xr.DataArray = xr.concat(bands, "band")
    # .assign_coords(
    #     coords={"band": np.array(range(3)) + 1}
    # )

    # Normalization to a [0, 1] float, as Sentinel reflectances value are given in the [[0, 10000]] range
    xds /= 10000.0

    # xds_lonlat = xds.rio.reproject("EPSG:4326")

    info(xds)
    info("anchor")
    info(xds.sel(band="B02"))  # selects the dimension
    info(xds.sel(band=["B02"]))  # keeps the englobing structure
    info(xds.sel(band=["B02", "B04"]))
    # info(xds_lonlat)

    """
    (Pdb) xds.rio.crs
    CRS.from_epsg(32631)
    (Pdb) xds_lonlat.rio.crs
    CRS.from_epsg(4326)
    """

    show(xds)

    return xds


def read_polygons(input_path: Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(input_path)
    info("===")
    info(gdf)
    gdf.plot()

    gdf = gdf.to_crs("32631")  # Not useful as we can pass the CRS to the rioxarray

    gdf.plot()

    return gdf


def show(xds):
    ax = xds.plot.imshow(vmax=np.percentile(xds, 99.5))
    ax.axes.set_aspect("equal")


def info(xds):

    logging.info(pformat(xds))  # TODO eschalk
    logging.info("--------")


def rasterize_geojson(
    data_array: xr.DataArray,
    training_classes: gpd.GeoDataFrame,
) -> xr.DataArray:
    xds = data_array
    gdf = training_classes

    burnt_polygons = rasterio.features.rasterize(
        (gdf, 4),
        out_shape=xds.shape[1:],
        fill=0,
        transform=xds.spatial_ref.GeoTransform.split(),
        dtype=np.uint8,
    )


def produce_clips(
    data_array: xr.DataArray,
    training_classes: gpd.GeoDataFrame,
    output: Path,
) -> None:
    # https://corteva.github.io/rioxarray/stable/examples/clip_geom.html#Clip-using-a-geometry
    # https://corteva.github.io/rioxarray/stable/examples/clip_geom.html#Clip-using-a-GeoDataFrame

    # https://rasterio.readthedocs.io/en/latest/topics/masking-by-shapefile.html
    # https://www.earthdatascience.org/courses/use-data-open-source-python/intro-vector-data-python/vector-data-processing/clip-vector-data-in-python-geopandas-shapely/
    # https://spatial-dev.guru/2022/09/15/clip-raster-by-polygon-geometry-in-python-using-rioxarray/

    # https://corteva.github.io/rioxarray/html/rioxarray.html#rioxarray.raster_array.RasterArray
    # https://corteva.github.io/rioxarray/html/rioxarray.html#rioxarray.raster_array.RasterArray.clip

    xds = data_array
    gdf = training_classes

    info("xds.spatial_ref")
    info(xds.spatial_ref)
    info(xds)
    info(gdf)
    # clipped, out_transform = mask(xds, gdf.geometry.values, invert=False)
    # https://gis.stackexchange.com/questions/401347/masking-raster-with-a-multipolygon

    # out_image, out_transform = rasterio.mask.mask(src, geo.geometry, filled = True)
    # out_image.plot()
    # # TODO eschalk flatten the mono-multipolygons to polygons before clipping as multipolygons are not supported
    # cropped = xds.rio.clip(geometries=gdf.geometry.values[0], crs=32631)

    # # cropped = xds.rio.clip(geometries=gdf.geometry.values[0], crs=4326)
    # clipped = cropped

    # info(clipped)

    # clipped.plot()

    # TODO eschalk
    # plt.show()
    burnt_polygons = rasterize_geojson(xds, gdf)



if __name__ == "__main__":
    main()
