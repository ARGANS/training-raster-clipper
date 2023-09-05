from pathlib import Path
from typing import Sequence, Tuple

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

from training_raster_clipper.custom_types import (
    BandNameType,
    ClassificationResult,
    ClassifiedSamples,
    Mapping,
    PolygonMask,
    ResolutionType,
)


def load_feature_polygons(input_path: Path) -> GeoDataFrame:
    return gpd.read_file(input_path).to_crs("32631")


def load_sentinel_data(
    sentinel_product_location: Path,
    resolution: ResolutionType,
    band_names: tuple[BandNameType, ...],
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
        band_name: list(
            sentinel_product_location.glob(
                f"GRANULE/*/IMG_DATA/R{resolution}m/*_{band_name}_*"
            )
        )[0]
        for band_name in band_names
    }

    rasters_type_unchecked = {
        band_name: rioxarray.open_rasterio(band_file_paths[band_name])
        for band_name in band_names
    }

    # Make the type system happy.
    # `open_rasterio` returns an Union, leaving it to the user to check for returned content.
    rasters = list(
        raster.assign_coords(coords={"band": [band_name]})
        for band_name, raster in rasters_type_unchecked.items()
        if isinstance(raster, xr.DataArray)
    )
    assert len(rasters) == len(rasters_type_unchecked)

    nodata_value = 0
    radio_add_offset = -1000.0
    quantification_value = 10000.0
    xda = xr.concat(rasters, "band")
    xda = xda.where(xda != nodata_value, np.float32(np.nan))

    # Normalization to the [0, 1] float, as Sentinel reflectances value are given in the [[0, 10000]] range
    return (xda + radio_add_offset) / quantification_value


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
    # TODO eschalk create a helper function to visualize rasters
    # TODO eschalk add an option to plot or not the data
    # TODO eschalk do the plt show just before exiting the script

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

    # Refining: get a list of (*band_names, feature class key) values
    # Note: `c_` concatenates the provided columns
    return np.concatenate(
        [
            np.c_[values, np.ones(len(values), dtype=np.float32) * feature_class]
            for feature_class, values in feature_class_to_rgb_values.items()
        ]
    )


def persist_to_csv(
    classified_rgb_rows: ClassifiedSamples,
    csv_output_path: Path,
    band_names: tuple[BandNameType, ...],
) -> None:
    df = pd.DataFrame(
        data=classified_rgb_rows,
        columns=[*(band_name for band_name in band_names), "feature_key"],
    )
    df.feature_key = df.feature_key.apply(int)
    df.to_csv(csv_output_path, index=False, sep=";")


def classify_sentinel_data(
    rasters: xr.DataArray, classified_rgb_rows: ClassifiedSamples
) -> ClassificationResult:
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

    # rasters.values is the underlying numpy array
    # The first dimension is the bands
    # The reshape extract the list of all reflectance values

    classes = model.predict(rasters.values.reshape(rasters["band"].size, -1).T).reshape(
        rasters.shape[1:]
    )

    return classes


def persist_classification_to_raster(
    raster_output_path: Path,
    rasters: xr.DataArray,
    classification_result: ClassificationResult,
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
