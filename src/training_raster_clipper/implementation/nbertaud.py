from pathlib import Path

import geopandas.io.file
import numpy as np
import pandas as pd
import rasterio.features
import rioxarray
import xarray as xr
from geopandas.geodataframe import GeoDataFrame
from sklearn.ensemble import RandomForestClassifier
import joblib

from training_raster_clipper.custom_types import (
    BandNameType,
    ClassificationResult,
    ClassifiedSamples,
    FeatureClassNameToId,
    PolygonMask,
    ResolutionType,
)


def load_feature_polygons(input_path: Path) -> GeoDataFrame:
    gdf = geopandas.io.file.read_file(input_path)
    gdf = gdf.to_crs(32631)
    return gdf


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

    # Find the path of the folder with the correct resolution
    spatial_resolution_location = list(sentinel_product_location.glob(f"GRANULE/*/IMG_DATA/R{resolution}m"))[0]

    # Find the path of the bands
    band_locations = {}
    for band_name in band_names:
        band_locations[band_name] = list(spatial_resolution_location.glob(f"*_{band_name}_*"))[0]

    # Read the band raster
    combined_data_array = []
    for band_name, raster in band_locations.items():
        band_data_array = rioxarray.open_rasterio(raster)
        band_data_array = band_data_array.assign_coords(coords={"band": [band_name]})
        combined_data_array.append(band_data_array)

    # Combine all the band in the same xarray
    combined_data_array = xr.concat(combined_data_array, "band")

    # Normalize the xarray
    SPECIAL_VALUE = 0
    RADIO_ADD_OFFSET = -1000
    QUANTIFICATION_VALUE = 10000
    normalized_data_array = combined_data_array.where(combined_data_array != SPECIAL_VALUE, np.nan)

    normalized_data_array = (normalized_data_array + RADIO_ADD_OFFSET) / QUANTIFICATION_VALUE

    return normalized_data_array


def rasterize_geojson(
    data_array: xr.DataArray,
    training_classes: GeoDataFrame,
) -> tuple[PolygonMask, FeatureClassNameToId]:
    """Burns a set of vectorial polygons to a raster.

    See https://gis.stackexchange.com/questions/316626/rasterio-features-rasterize

    Args:
        data_array (xr.DataArray): The Sentinel raster, from which data is taken, such as the transform or the shape.
        training_classes (GeoDataFrame): The input set of classified multipolygons to burn

    Returns:
        xr.DataArray: A mask raster generated from the polygons, representing the same geographical region as the source dataarray param
                      0 where no polygon were found, and integers representing classes in order of occurence in the GeoDataFrame
    """

    # Find transformation
    transform = np.array(data_array.spatial_ref.GeoTransform.split(" "), dtype=float)
    transform = rasterio.transform.Affine.from_gdal(*transform)

    # Find array shape
    array_shape = data_array.shape[1:]

    # Regroup class if in the GeoJSON file there are multiple instances of the same class
    dict_classes = {}
    for id in training_classes.index:
        current_class = training_classes["class"][id]

        if not(current_class in dict_classes):
            dict_classes[current_class] = []

        dict_classes[current_class].append(training_classes["geometry"][id])

    # Set a value for every class
    geometry_shape = []
    mapping = {}
    for index, current_class in enumerate(dict_classes.items()):
        mapping[current_class[0]] = index + 1
        for geometry in current_class[1]:
            geometry_shape.append((geometry, index + 1))

    return rasterio.features.rasterize(geometry_shape, array_shape, 0, transform=transform), mapping


def produce_clips(
    data_array: xr.DataArray, burnt_polygons: PolygonMask, mapping: FeatureClassNameToId
) -> ClassifiedSamples:
    """Extract RGB values covered by classified polygons

    Args:
        data_array (xr.DataArray): RGB raster
        burnt_polygons (PolygonMask): Rasterized classified multipolygons

    Returns:
        _type_: A list of the RGB values contained in the data_array and their corresponding classes
    """
    # Flatten list in (x,y) dimension
    band_array = data_array.stack(flatten=("y", "x"))
    class_array = xr.DataArray(burnt_polygons.reshape(-1), dims="flatten")

    # Fusion the arrays
    classified_dataset = xr.Dataset({"reflectance": band_array, "label": class_array})

    # Remove every element where class is not set
    classified_dataset = classified_dataset.sel(flatten=class_array != 0)

    return classified_dataset


def persist_to_csv(
    classified_rgb_rows: ClassifiedSamples,
    csv_output_path: Path,
) -> None:
    # Remove useless columns
    classified_rgb_rows = classified_rgb_rows.drop_vars(("x", "y", "spatial_ref"))

    # Get the correct dataframe
    reflectance_columns = classified_rgb_rows["reflectance"].T.to_pandas()
    label_column = classified_rgb_rows["label"].to_pandas()

    # Fusion both dataframe
    csv_dataset = pd.concat([reflectance_columns, label_column], axis=1)
    csv_dataset = csv_dataset.rename(columns={0: "label"})

    # Print csv
    csv_dataset.to_csv(csv_output_path, index=False)


def classify_sentinel_data(
    rasters: xr.DataArray, classified_rgb_rows: ClassifiedSamples
) -> ClassificationResult:

    # Instantiate model
    rf_clf = RandomForestClassifier()

    # Get training input and classification
    training_input_sample = classified_rgb_rows["reflectance"].T
    class_labels = classified_rgb_rows["label"]

    # Train the model
    rf_clf.fit(training_input_sample, class_labels)
    
    # # Save the model
    # joblib.dump(rf_clf, "path")
    # rf_clf = joblib.load("path")

    # Predict the classes of rasters
    rasters_numpy = rasters.values
    predictions = rf_clf.predict(rasters_numpy.reshape(4, -1).T)

    predictions = predictions.reshape(rasters_numpy.shape[1:])
    classification_result = rasters.isel(band=0).copy(data=predictions)

    return classification_result


def persist_classification_to_raster(
    raster_output_path: Path, classification_result: ClassificationResult
) -> None:
    classification_result.rio.to_raster(raster_output_path)
