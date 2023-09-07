from dataclasses import dataclass

from pathlib import Path

from training_raster_clipper.custom_types import (
    BandNameType,
    ClassifiedSamples,
    FeatureClassNameToId,
    PolygonMask,
    ResolutionType,
    ClassificationResult,
)
from typing import Callable
import geopandas as gpd

import xarray as xr


@dataclass(frozen=True, kw_only=True)
class TrainingConfiguration:
    verbose: bool
    show_plots: bool
    resolution: ResolutionType
    band_names: tuple[BandNameType, ...]
    raster_input_path: Path
    polygons_input_path: Path
    csv_output_path: Path
    raster_output_path: Path
    implementation_name: str

    # interface,
    # tutorial_step,


@dataclass(frozen=True, kw_only=True)
class TrainingFunctions:
    load_feature_polygons: Callable[[Path], gpd.GeoDataFrame]
    load_sentinel_data: Callable[
        [Path, ResolutionType, tuple[BandNameType, ...]], xr.DataArray
    ]
    rasterize_geojson: Callable[
        [xr.DataArray, gpd.GeoDataFrame], tuple[PolygonMask, FeatureClassNameToId]
    ]
    produce_clips: Callable[
        [xr.DataArray, PolygonMask, FeatureClassNameToId], ClassifiedSamples
    ]
    persist_to_csv: Callable[[ClassifiedSamples, Path], None]
    classify_sentinel_data: Callable[
        [xr.DataArray, ClassifiedSamples], ClassificationResult
    ]
    persist_classification_to_raster: Callable[[Path, ClassificationResult], None]
