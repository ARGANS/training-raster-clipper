from enum import Enum
from typing import Dict, Literal, Optional, Sequence

import numpy as np
import numpy.typing as npt

# Maps a feature class name to an integer.
Mapping = Dict[str, int]

# Rows of (*bands, class)
ClassifiedSamples = Sequence[Sequence[float]]

# Sparse 2D-matrix containing classes from polygons
PolygonMask = npt.NDArray[np.uint8]

# Allowed values for the Sentinel-2 Resolution
Resolution = Optional[Literal[60] | Literal[20] | Literal[10]]


class ColorVisible(Enum):
    RED = "B04"
    GREEN = "B03"
    BLUE = "B02"


class ColorVisibleAndNir(Enum):
    RED = "B04"
    GREEN = "B03"
    BLUE = "B02"
    NIR = "B8A"


Color = ColorVisibleAndNir
