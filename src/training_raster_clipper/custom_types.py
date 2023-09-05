from typing import Literal, Sequence

import numpy as np
import numpy.typing as npt

# Maps a feature class name to an integer.
Mapping = dict[str, int]

# Rows of (*bands, class)
ClassifiedSamples = npt.NDArray[np.float32]

# 2-D array of classes
ClassificationResult = npt.NDArray[np.int32]

# Sparse 2D-matrix containing classes from polygons
PolygonMask = npt.NDArray[np.uint8]

# Allowed values for the Sentinel-2 Resolution

# See Spatial Resolution https://sentinels.copernicus.eu/ca/web/sentinel/user-guides/sentinel-2-msi/resolutions/spatial
# See Sentinel-2 Spectral bands https://en.wikipedia.org/wiki/Sentinel-2#Spectral_bands
BandNameType = Literal[
    "B01",  # Coastal aerosol
    "B02",  # Blue
    "B03",  # Green
    "B04",  # Red
    "B05",  # Vegetation red edge
    "B06",  # Vegetation red edge
    "B07",  # Vegetation red edge
    "B08",  # NIR
    "B8A",  # Narrow NIR
    "B09",  # Water vapour
    "B10",  # SWIR – Cirrus
    "B11",  # SWIR
    "B12",  # SWIR
]
ResolutionType = Literal[10, 20, 60]
