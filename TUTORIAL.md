# Introduction to QGIS and Sentinel-2 Level-2 product processing with Python

QGIS is a software aimed at reading and manipulating geographical data, such as rasters and vectorial geometries.

The goal of this introduction is a 360-degrees round trip starting from reading then writing data with QGIS, reading this data with Python tools such as pandas, rasterio, rioxarray and processing it before finally visualizing the final result back in QGIS.

More concretely, this tutorial will make you do the following:

- Download and import a Sentinel-2 product in QGIS ;
- Draw geometric shapes to samples zones corresponding to water, farmland and forest ;
- Read the results from the two previous steps with Python ;
- Generate an intermediate data structure containing reflectance values (R, G, B, NIR) from the Sentinel-2 product intersected with the priorly defined classified polygons (water, farmland, forest) ;
- Feed this data structure to a machine learning model and use it to classify the pixels of the Sentinel-2 product ;
- Import the resulting raster into QGIS and visualize it.

It is recommended to watch and practice from this video beforehand : [QGIS User 0001 from Klas Karlsson](https://www.youtube.com/watch?v=RTjAp6dZ-DU) to first become more familiar with the QGIS user interface.

This introduction also assumes a prior minimal knowledge of the Python language : defining functions, list comprehensions, etc. Nevertheless, if you don't have this knowledge yet, be reassured, the language usage in this tutorial will be simple enough so anyone having a prior programming experience can follow along.

The Python code will be broken down in independant smaller functions, for easier progress tracking and debugging.

[TODO : provide typed function signatures as a starting point for the coding practice, to be filled by the tutorial follower]

[TODO export palette with python and auto import in QGIS]

Below is a preview of the result you will get, classifying water, farmland and forest. You can notice noise due to clouds in the top right of the image:

TODO eschalk show the legend for classes

![picture 5](images/7b19ac4eff434e8a00969011b0f58374e67a81cb080c1cfd11f276925da1e2a3.png)

## Table of Contents

- [Introduction to QGIS and Sentinel-2 Level-2 product processing with Python](#introduction-to-qgis-and-sentinel-2-level-2-product-processing-with-python)
  - [Table of Contents](#table-of-contents)
  - [Introduction to QGIS](#introduction-to-qgis)
    - [Download a Sentinel-2 product](#download-a-sentinel-2-product)
    - [Import a Sentinel-2 product into QGIS](#import-a-sentinel-2-product-into-qgis)
    - [Draw geometric shapes and classify them](#draw-geometric-shapes-and-classify-them)
      - [Export the polygons to the GeoJSON format](#export-the-polygons-to-the-geojson-format)
  - [Python](#python)
    - [Introduction](#introduction)
      - [Command line usage](#command-line-usage)
      - [High-level process](#high-level-process)
    - [Load a GeoJSON file (`geopanda`)](#load-a-geojson-file-geopanda)
      - [Expected result](#expected-result)
    - [Load a Sentinel-2 raster (`rioxarray`)](#load-a-sentinel-2-raster-rioxarray)
      - [Locate the interesting bands](#locate-the-interesting-bands)
      - [Use `rioxarray` to load the bands](#use-rioxarray-to-load-the-bands)
      - [Expected result](#expected-result-1)
    - [Rasterize the polygons](#rasterize-the-polygons)
      - [Overview](#overview)
      - [Rasterize the polygons](#rasterize-the-polygons-1)
      - [Expected result](#expected-result-2)
    - [Intersect the Sentinel-2 raster with polygons](#intersect-the-sentinel-2-raster-with-polygons)
      - [Expected result](#expected-result-3)
    - [Persist the intersection to a CSV](#persist-the-intersection-to-a-csv)
      - [Expected result](#expected-result-4)
    - [Train a machine learning model](#train-a-machine-learning-model)
      - [Expected result](#expected-result-5)
    - [Export the classification raster result](#export-the-classification-raster-result)
      - [Expected result](#expected-result-6)
  - [Back to QGIS](#back-to-qgis)
    - [Import the classification raster result](#import-the-classification-raster-result)
  - [Feedback](#feedback)

## Introduction to QGIS

### Download a Sentinel-2 product

Go to https://scihub.copernicus.eu/dhus/#/home. Note that you will need to create an account in order to access the data.

Use the selection tool too select a zone of interest. Here in this tutorial, we use a zone around Toulouse.

![picture 2](images/0d39faad45ac3d55e4e74c50872a45cda41572faf4d809c050f773db8cfff46a.png)  
_Selection of the zone of interest_

Fill in the search criteria :

- Here, we use a ~ 2-month time window for the _Sensing Period_: `[2022-11-01 ; 2022-12-12]`
- The _Ingestion Period_ is left empty
- Choose _Mission: Sentinel-2_
- _Satellite Platform_: `S2A_*`. The Sentinel-2 satellites work in pair. See [Sentinel-2](https://sentinel.esa.int/web/sentinel/missions/sentinel-2)
- _Product type_: `S2MSI2A`. This acronyms stands for Sentinel-2 MultiSpectral Instrument Level-2A. See [Product Types](https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-2-msi/product-types). Rule of thumb: higher numbers in the level means more user-friendly data.
- _Cloud Cover %_: `[0 TO 9.4]`. This helps filtering out images containing too many clouds, as they add unnecessary noise.
- _Relative Orbit Number_ is left empty

![picture 4](images/328f5e9bc29f1e87d047ba62300a06e5f2256470b15fb19c9bcd037bcc125d37.png)  
_Search criteria_

Click on the search button represented by a magnifier, and select a product covering the zone of interest. If you cannot find any, try first to increase the time window. You can then hit the download data.

![picture 3](images/e9e9c265dfeb095d5cd07be46c75e99812a85f1680d9583b1e08815145342a47.png)  
_Search Results_

Congratulations, you've downloaded your first Sentinel-2 product! In the screenshots, the downloaded file is an archived: `S2A_MSIL2A_20221116T105321_N0400_R051_T31TCJ_20221116T170958`

We find again some information in the filename: `S2A` = Sentinel-2A, `MSIL2A`= MultiSpectral Instrument Level-2A... More information on [Naming Convention](https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-2-msi/naming-convention)

In the next part we will visualize it into QGIS.

### Import a Sentinel-2 product into QGIS

[TODO eschalk]

### Draw geometric shapes and classify them

For each class (Water, Farmland and Forest), a unique MultiPolygon will be generated. A MultiPolygons is, without surprise, a collection of Polygons. Note that it is unordered. For more information, please refer to the [MultiPolygon section of the GeoJSON specification](https://www.rfc-editor.org/rfc/rfc7946#section-3.1.7)

[TODO eschalk]

#### Export the polygons to the GeoJSON format

## Python

### Introduction

#### Command line usage

The following commands will use bash. If you are a windows user with git installed, you can create a git bash shell from VSCode.

First, run `poetry install` to satisfy the dependencies required by the project.

To see the different arguments the script accept, run the following command from the project's root:

```bash
python ./training_raster_clipper/main.py -h
```

Below is an example of configuration:

```bash
TUTORIAL_STEP=NONE
POLYGONS_INPUT_PATH=
POLYGONS_INPUT_PATH=resources/solution/polygons.geojson
RASTER_INPUT_PATH=
RASTER_INPUT_PATH=D:/PROFILS/ESCHALK/DOWNLOADS/S2A_MSIL2A_20221116T105321_N0400_R051_T31TCJ_20221116T170958/S2A_MSIL2A_20221116T105321_N0400_R051_T31TCJ_20221116T170958.SAFE
CSV_OUTPUT_PATH=generated/classified_points.csv
RASTER_OUTPUT_PATH=generated/sklearn_raster.tiff

python ./training_raster_clipper/main.py -p $POLYGONS_INPUT_PATH -r $RASTER_INPUT_PATH -o $CSV_OUTPUT_PATH -s $RASTER_OUTPUT_PATH -v -t $TUTORIAL_STEP
```

As you can see, the first parameter corresponds to the step in the code we want to reach. Use this during the tutorial to make the script work until the intended step.

The next two are the paths to the input data, the GeoJSON polygons exported from QGIS as well as the location of the `.SAFE` file containing the Sentinel-2 product.

The two last ones, already provided, specify the location of the outputs of the script, a CSV file of classified pixels of the Sentinel-2 product and a raster resulting from the `sklearn` classification.

Note: you can see the final result by using the cheat flag (`-c`)

#### High-level process

![picture 6](images/fc792852fe7bc30966031a7cdc829e45c6ccb77558321d5fc78302ed6e1b0d13.png)

### Load a GeoJSON file (`geopanda`)

```python
def load_feature_polygons(input_path: Path) -> GeoDataFrame:
```

In this step, we read from a GeoJSON file and load the data to a `GeoDataFrame` from `geopanda`. See [read_file](https://geopandas.org/en/stable/docs/reference/api/geopandas.read_file.html)

The `geopanda` library adds geographical capabilities over `pandas`, such as a `geometry` column containing the description of the geographical feature. The rest of the columns are retrieved from the GeoJSON metadata.

Since the GeoJSON is in a `4326` EPSG format, we convert it to the one used by the Sentinel-2 raster: `32631`. See [to_crs](https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoDataFrame.to_crs.html)

:arrow_forward: Return the GeoDataFrame representing the data contained in your GeoJSON file.

#### Expected result

```log
INFO:root:Executing step: TutorialStep.LOAD_FEATURE_POLYGONS
INFO:root:     id   class                                           geometry
0  None   WATER  MULTIPOLYGON (((366356.635 4843608.195, 366742...
1  None  FOREST  MULTIPOLYGON (((355918.751 4834466.232, 357404...
2  None    FARM  MULTIPOLYGON (((365718.363 4843753.544, 365876...
```

:eyes: We can see again our 3 MultiPolygons created from QGIS, each of them corresponding to a specific class

### Load a Sentinel-2 raster (`rioxarray`)

```python
def load_sentinel_data(
    sentinel_product_location: Path,
    resolution: Resolution = 60,
) -> xr.DataArray:
```

In this tutorial, we will use a resolution of 60 meters, the minimal available one, to use less memory and iterate faster.

#### Locate the interesting bands

You can see in the `custom_types/custom_types.py` file that the following enum is defined:

```python
class ColorVisibleAndNir(Enum):
    RED = "B04"
    GREEN = "B03"
    BLUE = "B02"
    NIR = "B8A"


Color = ColorVisibleAndNir
```

:information_source: The values of this enum correspond to the band names as described in [Spatial Resolution](https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-2-msi/resolutions/spatial). The noun "Color" is here used more broadly, as it also includes the NIR (Near Infrared). A more correct name would be "Band".

The glob pattern to locate the files from the `.SAFE` folder containing the Sentinel-2 product is the following: `GRANULE/*/IMG_DATA/R{resolution}m/*_{color.value}_*`

:arrow_forward: Generate a color-indexed `Dict` of paths pointing to a raster for all colors in the `Color` enum

#### Use `rioxarray` to load the bands

:arrow_forward: Generate a list of [`xarray.DataArray`](https://docs.xarray.dev/en/stable/generated/xarray.DataArray.html) Use [`rioxarray.open_rasterio`](https://corteva.github.io/rioxarray/stable/rioxarray.html#rioxarray-open-rasterio).

Each DataArray should be cast to float, as the Sentinel values are integer-encoded, [ranging from 0 to 10000](https://docs.sentinel-hub.com/api/latest/data/sentinel-2-l2a/#harmonize-values). They actually represent a reflectance value from 0 to 1, so to normalize, the values in the DataArray must be divided by 10000.

Each DataArray should be enhanced with a new "band" coord, with the value being the one from the `Color` enum. See [`xarray.DataArray.assign_coords`](https://docs.xarray.dev/en/stable/generated/xarray.DataArray.assign_coords.html)

:arrow_forward: Concatenate the bands on a "band" dimension, using [xarray.concat](https://docs.xarray.dev/en/stable/generated/xarray.concat.html) for all colors in the `Color` enum. The final DataArray should have 3 coordinates: band, x, y.

#### Expected result

```log
INFO:root:Executing step: TutorialStep.LOAD_SENTINEL_DATA
INFO:root:<xarray.DataArray (band: 4, y: 1830, x: 1830)>
array([[[0.172 , 0.1677, 0.1614, ..., 0.1329, 0.1313, 0.1291],
        [0.171 , 0.1666, 0.1674, ..., 0.1315, 0.1296, 0.1329],
        [0.1797, 0.1531, 0.1551, ..., 0.1305, 0.1296, 0.1344],
        ...,
        [0.1353, 0.1321, 0.1216, ..., 0.1713, 0.1412, 0.1603],
        [0.116 , 0.1325, 0.1314, ..., 0.2727, 0.263 , 0.208 ],
        [0.1248, 0.1357, 0.1402, ..., 0.2427, 0.233 , 0.248 ]],

       [[0.1611, 0.1578, 0.15  , ..., 0.1461, 0.1437, 0.1419],
        [0.1606, 0.1509, 0.148 , ..., 0.144 , 0.1402, 0.144 ],
        [0.1603, 0.1463, 0.1462, ..., 0.1426, 0.142 , 0.1465],
        ...,
        [0.139 , 0.143 , 0.1325, ..., 0.1606, 0.1412, 0.1514],
        [0.1243, 0.1442, 0.1474, ..., 0.2279, 0.2241, 0.1886],
        [0.1347, 0.1467, 0.1508, ..., 0.2062, 0.1989, 0.2136]],

       [[0.1347, 0.1323, 0.1276, ..., 0.1134, 0.1132, 0.1132],
        [0.1341, 0.1304, 0.1288, ..., 0.1135, 0.1129, 0.1146],
        [0.1349, 0.1231, 0.1257, ..., 0.1129, 0.1131, 0.1165],
        ...,
        [0.1115, 0.1115, 0.1037, ..., 0.1236, 0.1136, 0.1218],
        [0.1035, 0.1131, 0.1105, ..., 0.16  , 0.1596, 0.145 ],
        [0.1076, 0.1156, 0.1158, ..., 0.1488, 0.1453, 0.1577]],

       [[0.2769, 0.277 , 0.2587, ..., 0.3713, 0.3631, 0.3439],
        [0.276 , 0.2345, 0.2191, ..., 0.3511, 0.3403, 0.3547],
        [0.2519, 0.2613, 0.2484, ..., 0.3485, 0.3559, 0.3687],
        ...,
        [0.3279, 0.3605, 0.3403, ..., 0.3368, 0.3274, 0.3498],
        [0.2775, 0.4015, 0.4392, ..., 0.3312, 0.3428, 0.3548],
        [0.4155, 0.4093, 0.4304, ..., 0.2904, 0.2792, 0.2992]]])
Coordinates:
  * band         (band) <U3 'B04' 'B03' 'B02' 'B8A'
  * x            (x) float64 3e+05 3.001e+05 3.002e+05 ... 4.097e+05 4.098e+05
  * y            (y) float64 4.9e+06 4.9e+06 4.9e+06 ... 4.79e+06 4.79e+06
    spatial_ref  int32 0
```

### Rasterize the polygons

```python
def rasterize_geojson(
    data_array: xr.DataArray,
    training_classes: GeoDataFrame,
) -> Tuple[PolygonMask, Mapping]:
```

This step uses data from the two previous steps: the metadata from the multi-band DataArray obtained with Sentinel-2 data, and the polygons loaded from the GeoJSON file into a GeoDataFrame.

Please note that the mapping should only contain strictly positive integers, as `0` cells will be treated as "empty".

The goal is to obtain a raster mask that will be later used to extract the reflectance data of pixels overlapping the classified polygons. This data can then be fed to a machine learning model to classify the rest of the pixels of the original Sentinel-2 data. The reflectance will be the "samples", and the classes the "features". Trained with a few samples, we want the model to be able to assign a "feature" to every pixel of the original Sentinel-2 image.

#### Overview

![picture 9](images/62eca0e5f6d56e6875bc55e0ae774de006d479b03be976061a117e3a05c1992e.png)

#### Rasterize the polygons

`rasterio` provides a method to realize the desired output raster of polygons: [rasterio.features.rasterize](https://rasterio.readthedocs.io/en/latest/api/rasterio.features.html#rasterio.features.rasterize). The documentation tells the required parameters. You will need:

- From the DataArray:
  - the transform available under the `spatial_ref` dimension
  - the shape, available directly under the `shape` number, without "band" (only "x" and "y")
- From the GeoDataFrame:
  - the `geometry` column,
  - the `class` column,
  - and the `index` column (can be used to generate the integer mapping)

:arrow_forward: Generate the rasterized polygons according to their class. Return a tuple with the rasterized polygons + the generated integer mapping.

#### Expected result

```log
INFO:root:Executing step: TutorialStep.RASTERIZE_GEOJSON
INFO:root:array([[0, 0, 0, ..., 0, 0, 0],
       [0, 0, 0, ..., 0, 0, 0],
       [0, 0, 0, ..., 0, 0, 0],
       ...,
       [0, 0, 0, ..., 0, 0, 0],
       [0, 0, 0, ..., 0, 0, 0],
       [0, 0, 0, ..., 0, 0, 0]], dtype=uint8)
INFO:root:{'FARM': 3, 'FOREST': 2, 'WATER': 1}
```

### Intersect the Sentinel-2 raster with polygons

[TODO eschalk]

```python
def produce_clips(
    data_array: xr.DataArray, burnt_polygons: PolygonMask, mapping: Mapping
) -> ClassifiedSamples:
```

The goal of this step is to extract the reflectance values of all pixels of the Sentinel-2 data intersecting with a polygon, assign them to the corresponding polygon's class, and so for all bands. The result is basically a table, with columns containing reflectance values of all bands, and a column containing the class of the pixel coming from the overlapping polygon.

:arrow_forward: Return this table.

#### Expected result

```log
INFO:root:Executing step: TutorialStep.PRODUCE_CLIPS
INFO:root:array([[0.107 , 0.1152, 0.1041, 0.1073, 1.    ],
       [0.1071, 0.1148, 0.1036, 0.1173, 1.    ],
       [0.1097, 0.1175, 0.1047, 0.13  , 1.    ],
       ...,
       [0.1963, 0.1785, 0.1435, 0.3284, 3.    ],
       [0.2053, 0.1794, 0.1456, 0.3005, 3.    ],
       [0.2078, 0.1793, 0.1443, 0.2912, 3.    ]])
```

### Persist the intersection to a CSV

```python
def persist_to_csv(
    classified_rgb_rows: ClassifiedSamples,
    csv_output_path: Path,
) -> None:
```

:arrow_forward: With the help of a pandas DataFrame, output the previously obtained numpy array of colors and class to a CSV File. Columns must be all the Colors, followed by the integer representing the class of the pixel.

#### Expected result

```log
INFO:root:Executing step: TutorialStep.PERSIST_TO_CSV
INFO:root:Written CSV output generated\classified_points.csv
```

Excerpt from an example of a generated file:

```csv
B04;B03;B02;B8A;feature_key
0.107;0.1152;0.1041;0.1073;1
0.1071;0.1148;0.1036;0.1173;1
0.1097;0.1175;0.1047;0.13;1
...
0.1233;0.1262;0.1043;0.3333;2
0.1332;0.1342;0.1101;0.3446;2
0.1283;0.1336;0.1085;0.3442;2
...
0.1963;0.1785;0.1435;0.3284;3
0.2053;0.1794;0.1456;0.3005;3
0.2078;0.1793;0.1443;0.2912;3
```

### Train a machine learning model

[TODO eschalk]

```python
def classify_sentinel_data(
    rasters: xr.DataArray,
    classified_rgb_rows: ClassifiedSamples
) -> np.ndarray:
```

We will now use the tools provided by `scikit-learn` to classify the rest of the pixels of the Sentinel rasters.

#### Expected result

```log
INFO:root:Executing step: TutorialStep.CLASSIFY_SENTINEL_DATA
INFO:root:array([[3, 3, 3, ..., 2, 2, 2],
       [3, 3, 3, ..., 2, 2, 2],
       [3, 2, 2, ..., 2, 2, 2],
       ...,
       [2, 2, 2, ..., 3, 2, 2],
       [2, 2, 2, ..., 3, 3, 3],
       [2, 2, 3, ..., 3, 3, 3]])
```

~~### Add the NIR band to get better results~~

~~The goal of this part is to show that using the NIR (Near-Infrared) band can help identify water and provide better classification results. The subsidiary goal is to show that with a flexible enough code, loading this NIR band should be as simple as adding a new value in the `Color` enum.~~

_Note: Removed because the NIR band is included from the start_

### Export the classification raster result

```python
def persist_classification_to_raster(
    raster_output_path: Path, rasters: xr.DataArray, classification_result: np.ndarray
) -> None:
```

TODO eschalk
The main difficulty here is to reconstruct a new raster from the classification result and the original sentinel raster.

:arrow_forward: Create an [`xarray.DataArray`](https://docs.xarray.dev/en/stable/generated/xarray.DataArray.html) from the classification result. Reuse the "x" and "y" `coords` from the original sentinel raster. :warning" Assign `dims` in the correct order ("y" then "x").

:arrow_forward: Set the CRS based on the `crs_wkt` attribute of the `spatial_ref` dim of the original sentinel raster. For this, use [`write_crs`](https://corteva.github.io/rioxarray/stable/rioxarray.html#rioxarray.rioxarray.XRasterBase.write_crs) from the `rio` accessor. This accessor is added on `xarray.DataArray`s by the `rioxarray` extension.

:arrow_forward: Persist the `xarray.DataArray` to a raster, using the [to_raster](https://corteva.github.io/rioxarray/stable/rioxarray.html#rioxarray.raster_array.RasterArray.to_raster) from the `rio` accessor

#### Expected result

```log
INFO:root:Executing step: TutorialStep.PERSIST_CLASSIFICATION_TO_RASTER
INFO:root:Written Classified Raster to generated\classified_points.csv
INFO:root:Congratulations, you reached the end of the tutorial!
```

## Back to QGIS

### Import the classification raster result

## Feedback

If you have any questions or feedback regarding this tutorial, please contact me (Etienne) or Pierre
