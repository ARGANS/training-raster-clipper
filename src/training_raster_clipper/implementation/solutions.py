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
from rasterio.features import rasterize
from sklearn.ensemble import RandomForestClassifier

from training_raster_clipper.custom_types import (
    BandNameType,
    ClassificationResult,
    ClassifiedSamples,
    FeatureClassNameToId,
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

    xda = xr.concat(rasters, "band")

    nodata_value = 0
    radio_add_offset = -1000.0
    quantification_value = 10000.0
    xda = xda.where(xda != nodata_value, np.float32(np.nan))

    # Normalization to the [0, 1] float, as Sentinel reflectances value are given in the [[0, 10000]] range
    return (xda + radio_add_offset) / quantification_value


def rasterize_geojson(
    data_array: xr.DataArray,
    training_classes: GeoDataFrame,
) -> Tuple[PolygonMask, FeatureClassNameToId]:
    """Burns a set of vectorial polygons to a raster.

    See https://gis.stackexchange.com/questions/316626/rasterio-features-rasterize

    Args:
        data_array (xr.DataArray): The Sentinel raster, from which data is taken, such as the transform or the shape.
        training_classes (GeoDataFrame): The input set of classified multipolygons to burn

    Returns:
        xr.DataArray: A mask raster generated from the polygons, representing the same geographical region as the source dataarray param
                      0 where no polygon were found, and integers representing classes in order of occurence in the GeoDataFrame
    """

    xda = data_array
    gdf = training_classes

    # plt.imshow(xds[:-1].values)
    # TODO eschalk create a helper function to visualize rasters
    # TODO eschalk add an option to plot or not the data
    # TODO eschalk do the plt show just before exiting the script

    raster_transform = list(float(k) for k in xda.spatial_ref.GeoTransform.split())
    raster_transform = Affine.from_gdal(*raster_transform)

    # Get the shape of a band-slice. isel 0 means "take the first one"
    # Drop true means we are not interested to keep the remaining band coord.
    out_shape = xda.isel(band=0, drop=True).shape

    # Extract couples of geometry and class required to rasterize
    # shapes = [(row.geometry, row.class_key) for _, row in gdf.iterrows()]
    shapes = list(zip(gdf.geometry, gdf.index + 1))
    mapping = dict(zip(gdf["class"].values, gdf.index + 1))

    burnt_polygons: PolygonMask = rasterize(
        shapes,
        out_shape=out_shape,
        fill=0,
        transform=raster_transform,
        dtype=np.uint8,
    )

    return burnt_polygons, mapping


def produce_clips(
    data_array: xr.DataArray, burnt_polygons: PolygonMask, mapping: FeatureClassNameToId
) -> ClassifiedSamples:
    """Extract RGB values covered by classified polygons

    Args:
        data_array (xr.DataArray): RGB raster
        burnt_polygons (PolygonMask): Rasterized classified multipolygons

    Returns:
        A list of the RGB values contained in the data_array and their corresponding classes
    """

    xda = data_array

    # Wrap the polygons' numpy array into an xarray DataArray fore easier work.
    # Copy a band-slice of the reflectances and use the polygons data instead.
    # The general pattern "isel coord = 0" means, we just want to extract a
    # representative slice of the data cube.
    burnt_polygons_xda = xda.isel(band=0, drop=True).copy(data=burnt_polygons)

    # Extract reflectance values for all bands of all indices matching the predicate:
    # "the polygon mask matches the current class in the loop".
    # The stack method is used to "compress" the y and x dimension to a new 1-D z ones,
    # allowing for selection using `sel`, avoiding the more heavy `where`.
    # It avoids having to deal with the NaNs that `where` produce.
    feature_id_to_reflectances = {
        feature_id: (
            xda.stack(z=("y", "x")).sel(
                z=burnt_polygons_xda.stack(z=("y", "x")) == feature_id
            )
            # We won't need spatial information anymore
            .drop_vars(("y", "x", "spatial_ref"))
        )
        for feature_id in mapping.values()
    }

    # The dataset contains two variables:
    # - The original reflectances, (band, z)-dependant
    # - The feature class the pixels belong to, z-dependant
    # This will be fed as an input to the model later.
    classified_samples_dataset = xr.concat(
        (
            xr.Dataset(
                {
                    "reflectance": reflectances,
                    "feature_id": xr.ones_like(reflectances.z) * feature_id,
                }
            )
            for feature_id, reflectances in feature_id_to_reflectances.items()
        ),
        dim="z",
    )

    return classified_samples_dataset


def persist_to_csv(
    classified_rgb_rows: ClassifiedSamples,
    csv_output_path: Path,
) -> None:
    df = classified_rgb_rows["reflectance"].T.to_pandas()
    df["feature_id"] = classified_rgb_rows["feature_id"].to_series()
    df.to_csv(csv_output_path, index=False, sep=";")


def classify_sentinel_data(
    rasters: xr.DataArray, classified_rgb_rows: ClassifiedSamples
) -> ClassificationResult:
    model = RandomForestClassifier()

    # Remainder: Shape of the classified_rgb_rows array:
    # B04;B03;B02;B8A;feature_id
    # 0.107;0.1152;0.1041;0.1073;1

    training_input_samples = classified_rgb_rows["reflectance"].T
    class_labels = classified_rgb_rows["feature_id"]

    model.fit(training_input_samples, class_labels)

    reference_2d_array = rasters.isel(band=0, drop=True)

    classes = model.predict(rasters.stack(z=("y", "x")).T)

    classes_xda = reference_2d_array.copy(
        data=classes.reshape(reference_2d_array.shape)
    )
    return classes_xda


def persist_classification_to_raster(
    raster_output_path: Path, classification_result: ClassificationResult
) -> None:
    classification_result.rio.to_raster(raster_output_path)
