from pathlib import Path

import xarray as xr
from geopandas.geodataframe import GeoDataFrame
from rioxarray import open_rasterio
from geopandas import read_file
import numpy as np
from training_raster_clipper.custom_types import (
    BandNameType,
    ClassificationResult,
    ClassifiedSamples,
    FeatureClassNameToId,
    PolygonMask,
    ResolutionType,
)


def load_feature_polygons(input_path: Path) -> GeoDataFrame:
    geodf = read_file(input_path)
    return GeoDataFrame(geodf, crs=4326)


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
    RADIO_ADD_OFFSET = -1000
    QUANTIFICATION_VALUE = 10000

    dict_bands = {}
    if len(band_names) == 0:
        return print("no bands selected")
    for band in band_names:
        dict_bands[band] = sorted(
            Path(sentinel_product_location).glob(
                f"GRANULE/*/IMG_DATA/R{resolution}m/*_{band}_*"
            )
        )[0]

    list_dataarray = []

    for band_name, raster_path in dict_bands.items():
        raster = open_rasterio(raster_path)

        list_dataarray.append(raster.assign_coords({"band": [band_name]}))

    rasters_concat = xr.concat(list_dataarray, dim="band")

    result = rasters_concat.where(
        rasters_concat != 0,
        np.float32(np.NaN),
    )

    result = (result - RADIO_ADD_OFFSET) / QUANTIFICATION_VALUE

    return result


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

    ...  # TODO
    raise NotImplementedError


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

    ...  # TODO
    raise NotImplementedError


def persist_to_csv(
    classified_rgb_rows: ClassifiedSamples,
    csv_output_path: Path,
) -> None:
    ...  # TODO
    raise NotImplementedError


def classify_sentinel_data(
    rasters: xr.DataArray, classified_rgb_rows: ClassifiedSamples
) -> ClassificationResult:
    ...  # TODO
    raise NotImplementedError


def persist_classification_to_raster(
    raster_output_path: Path, classification_result: ClassificationResult
) -> None:
    ...  # TODO
    raise NotImplementedError
