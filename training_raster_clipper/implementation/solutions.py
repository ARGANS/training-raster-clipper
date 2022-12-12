import argparse
import logging
from enum import Enum
from pathlib import Path
from pprint import pformat
from typing import Tuple, Sequence

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

from custom_types.custom_types import (
    ClassifiedSamples,
    Color,
    Mapping,
    PolygonMask,
    Resolution,
)


def load_feature_polygons(input_path: Path) -> GeoDataFrame:

    return gpd.read_file(input_path).to_crs("32631")


def load_sentinel_data(
    sentinel_product_location: Path,
    resolution: Resolution = 60,
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
        for color in Color
    )

    xds: xr.DataArray = xr.concat(bands, "band")

    # Normalization to a [0, 1] float, as Sentinel reflectances value are given in the [[0, 10000]] range
    return xds / 10000.0


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

    xds = data_array
    gdf = training_classes

    # plt.imshow(xds[:-1].values)
    breakpoint()
    ax = xds[:-1].plot.imshow(vmax=np.percentile(xds, 99.5))
    ax.axes.set_aspect("equal")
    plt.show()

    raster_transform = list(float(k) for k in xds.spatial_ref.GeoTransform.split())
    raster_transform = Affine.from_gdal(*raster_transform)

    # Remove the first value (band) and keep the dimensional ones
    out_shape = xds.shape[1:]

    # Extract couples of geometry and class required to rasterize
    # shapes = [(row.geometry, row.class_key) for _, row in gdf.iterrows()]
    shapes = list(zip(gdf.geometry, gdf.index + 1))
    mapping = dict(zip(gdf["class"], gdf.index + 1))
    # print(mapping)

    # ndarray means n-dimensional array
    burnt_polygons: PolygonMask = rasterio.features.rasterize(
        shapes,
        out_shape=out_shape,
        fill=0,
        transform=raster_transform,
        dtype=np.uint8,
    )

    # plt.imshow(burnt_polygons)
    # plt.show()
    return burnt_polygons, mapping


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

    xds = data_array

    # The first colon allows to work on all bands.
    # The remaining filtering is used to extract reflectance values (for all bands)
    # of all 2D indices matching the predicate:
    # the polygon mask matches the current class in the loop
    feature_class_to_rgb_values = {
        c: xds.values[:, burnt_polygons == c].T for c in mapping.values()
    }

    # Refining: get a list of (R, G, B, feature class key) values
    # Note: `c_` concatenated the provided columns
    return np.concatenate(
        [
            np.c_[values, np.ones(len(values)) * feature_class]
            for feature_class, values in feature_class_to_rgb_values.items()
        ]
    )


def persist_to_csv(
    classified_rgb_rows: ClassifiedSamples,
    csv_output_path: Path,
) -> None:

    df = pd.DataFrame(
        data=classified_rgb_rows,
        columns=[*(color.value for color in Color), "feature_key"],
    )
    df.feature_key = df.feature_key.apply(int)
    df.to_csv(csv_output_path, index=False, sep=";")


def classify_sentinel_data(
    rasters: xr.DataArray, classified_rgb_rows: ClassifiedSamples
) -> np.ndarray:

    model = RandomForestClassifier()

    # Remainder: Shape of the classified_rgb_rows array:
    #
    # B04;B03;B02;B8A;feature_key
    # 0.107;0.1152;0.1041;0.1073;1
    #
    # classified_rgb_rows[:, : len(Color)] = B04;B03;B02;B8A
    # classified_rgb_rows[:, -1] = feature_key

    training_input_samples = classified_rgb_rows[:, :-1]
    class_labels = classified_rgb_rows[:, -1].astype(int)

    model.fit(training_input_samples, class_labels)
    classes = model.predict(rasters.values.reshape(len(Color), -1).T).reshape(
        rasters.shape[1:]
    )
    plt.imshow(classes)
    plt.show()
    return classes


def persist_classification_to_raster(
    raster_output_path: Path, rasters: xr.DataArray, classification_result: np.ndarray
) -> None:

    # Build a new raster from the result data array + the original sentinel raster
    data_array = xr.DataArray(
        classification_result,
        coords={
            "x": rasters.coords["x"],
            "y": rasters.coords["y"],
        },
        dims=["y", "x"],
    ).rio.write_crs(rasters.spatial_ref.crs_wkt)

    # Persist
    data_array.rio.to_raster(raster_output_path)
