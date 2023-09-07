from pathlib import Path

import xarray as xr
from geopandas.geodataframe import GeoDataFrame
from geopandas import read_file
from rioxarray import open_rasterio
import numpy as np

xr.set_options(keep_attrs=True)

from training_raster_clipper.custom_types import (
    BandNameType,
    ClassificationResult,
    ClassifiedSamples,
    FeatureClassNameToId,
    PolygonMask,
    ResolutionType,
)


def load_feature_polygons(input_path: Path) -> GeoDataFrame:
    # ...  # TODO
    gdf = read_file(input_path)
    gdf = gdf.to_crs(32631)
    return gdf
    # raise NotImplementedError


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

    # ...  # TODO
    # raise NotImplementedError
    # p = Path(sentinel_product_location)
    # paths_list = [x for x in p.iterdir() if x.is_file()]
    # colors_list = [str(x).split('_')[-2] for x in paths_list]
    # data_dict = dict(zip(colors_list, paths_list))
    # data_arrays_list = 
    paths_list = {
        band_name : list(sentinel_product_location.glob(f'GRANULE/*/IMG_DATA/R{resolution}m/*_{band_name}_*'))[0]
        for band_name in band_names
    }
    data_arrays_list = [open_rasterio(paths_list[band_name]).assign_coords({'band' : [band_name]}) for band_name in band_names]
    rasters_data_array = xr.concat(data_arrays_list, dim = 'band')
    rasters_data_array = rasters_data_array.where(rasters_data_array != 0, np.float32(np.nan))
    RADIO_ADD_OFFSET = -1000
    QUANTIFICATION_VALUE = 10000
    result = ((rasters_data_array + RADIO_ADD_OFFSET) / QUANTIFICATION_VALUE)
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
