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

Below is a preview of the result you will get, classifying water, farmland and forest. You can notice noise due to clouds in the top right of the image:

![picture 5](images/7b19ac4eff434e8a00969011b0f58374e67a81cb080c1cfd11f276925da1e2a3.png)

## Table of Contents

- [Introduction to QGIS and Sentinel-2 Level-2 product processing with Python](#introduction-to-qgis-and-sentinel-2-level-2-product-processing-with-python)
  - [Table of Contents](#table-of-contents)
  - [Introduction to QGIS](#introduction-to-qgis)
    - [Download a Sentinel-2 product](#download-a-sentinel-2-product)
    - [Import a Sentinel-2 product into QGIS](#import-a-sentinel-2-product-into-qgis)
      - [Files to import](#files-to-import)
      - [Operations in QGIS](#operations-in-qgis)
    - [Draw geometric shapes and classify them](#draw-geometric-shapes-and-classify-them)
      - [Export the polygons to the GeoJSON format](#export-the-polygons-to-the-geojson-format)
  - [Python](#python)
    - [Introduction](#introduction)
      - [Command line usage](#command-line-usage)
      - [`launch.sh` script](#launchsh-script)
      - [Write your own code](#write-your-own-code)
      - [High-level process](#high-level-process)
    - [(1) Load a GeoJSON file with `geopanda`](#1-load-a-geojson-file-with-geopanda)
      - [Expected result](#expected-result)
    - [(2) Load a Sentinel-2 raster with `rioxarray`](#2-load-a-sentinel-2-raster-with-rioxarray)
      - [Locate the interesting bands](#locate-the-interesting-bands)
      - [Use `rioxarray` to load the bands](#use-rioxarray-to-load-the-bands)
      - [Expected result](#expected-result-1)
    - [(3) Rasterize the polygons](#3-rasterize-the-polygons)
      - [Overview](#overview)
      - [Rasterize the polygons](#rasterize-the-polygons)
      - [Expected result](#expected-result-2)
    - [(4) Intersect the Sentinel-2 raster with polygons](#4-intersect-the-sentinel-2-raster-with-polygons)
      - [Expected result](#expected-result-3)
    - [(5) Persist the intersection to a CSV](#5-persist-the-intersection-to-a-csv)
      - [Expected result](#expected-result-4)
    - [(6) Train a machine learning model](#6-train-a-machine-learning-model)
      - [Expected result](#expected-result-5)
    - [(7) Export the classification raster result](#7-export-the-classification-raster-result)
      - [Expected result](#expected-result-6)
  - [Back to QGIS](#back-to-qgis)
    - [Import the classification raster result](#import-the-classification-raster-result)
  - [Feedback](#feedback)
  - [Improvements ideas](#improvements-ideas)
  - [Tout Doux](#tout-doux)

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

:information_source: If for some reason you cannot download the Sentinel-2 product, a set of the minimal files required to continue the tutorial is available under: `resources/solution/example_sentinel_files/SENTINEL.SAFE/GRANULE/L2A_T31TCJ_A038658_20221116T105603/IMG_DATA/R60m`

### Import a Sentinel-2 product into QGIS

#### Files to import

This first step is to import the interesting products from the Sentinel-2 `.SAFE` file.

The rasters of interest will be located in this folder: `GRANULE/*/IMG_DATA/R60m`. You can notice that we will use a 60m resolution, the lowest one. But you can also import others if you want to.

First, use the TCI file. It contains the Red, Blue and Green bands and can be visualized neatly into QGIS without further processing.

Then, import the bands of interest separately: Red, Green, Blue, as well as the NIR band. We will import these files in the python code coming next.

:information_source: The [Spatial Resolution](https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-2-msi/resolutions/spatial) page gives information on which files to choose:

- RED = "B04"
- GREEN = "B03"
- BLUE = "B02"
- NIR = "B8A"

#### Operations in QGIS

Create a new project in QGIS. For each of the files of interest, import them to a new Raster layer:

Layer > Add Layer > Add Raster Layer. Select the source then click Add, closing the pop-up window.

![picture 12](images/961e0e8cc014b9ce4d4025aaf0d72092344b42a632ea78daf520f79e157efcc5.png)

![picture 13](images/637ce2ecd41e79d963a87b839ef1096c9be6d0dbc26730692510b3f176337144.png)

You can change the default gray color palette to get a more visually interesting one. Right click on the Layer, choose Properties, then go to Symbology, then Band Rendering > Render type > Singleband pseudocolor. Then, under Color ramp, choose a more visually appealing one, eg Magma. Note that the TCI file contains all RGB bands and can be visualized instantly

_Different Sentinel-2 files imported as Raster Layers_

### Draw geometric shapes and classify them

For each class (Water, Farmland and Forest), a unique MultiPolygon will be generated. A MultiPolygons is, without surprise, a collection of Polygons. Note that it is unordered. For more information, please refer to the [MultiPolygon section of the GeoJSON specification](https://www.rfc-editor.org/rfc/rfc7946#section-3.1.7)

Layer > Create Layer > New Shapefile Layer.

Choose the location where you want to save the file, choose Polygon as a geomtry type, and add 2 text fields:

- class: will correspond to the feature covered by the polygon: WATER, FARMLAND, FOREST
- color: will be used to assign neat colors to the classes (eg `#0000ff` for blue)

![picture 15](images/00efd93eae6ea23e069fb222fd3a16e3eb301804d0207fdd40b7e0e1e566abcb.png)

Edit the layer:

![picture 16](images/f8269b26af42670b2179d79cad9541fc50636b7fa45dd269a52825ff90269898.png)

_Add a Polygon covering a water surface, with WATER as a class and a Blue color_

_Select the created polygon_

![picture 20](images/62d6c71fb7f9820b1d9ece858d76505e4b588a681e42237354e07e78884b3d72.png)

_Add Part tool will make you de facto create a to-be MultiPolygon for the JSON format_

![picture 22](images/4ce2614fb0b14dd51fdfb96dbd278c73eefb0a5943a10e6bba8233df5b89d490.png)

_A MultiPolygon with 2 parts, classified as WATER_

Do the same for FARMLAND and FOREST.

You can show the polygons in different colors according to their class (and color) by using:
Polygons layer properties > Symbology > Choose Categorized

Then, use `color` as a Value, and click on Classify.

Random colors are assigned, but there is a smarter way so we can use the already defined colors from the color field. For each category: Double click to open the "Edit rule" menu, then select the "Simple Fill", Fill Color > Field type: string and select `color`:

![picture 26](images/0bdea8086886ca35a2e99111516a41d355af8a190d6e5b22f547e3af8e960090.png)

![picture 28](images/55f60420d6590ec1a690c6dbaebc73b82eb63de86e6c56d03181786ba407418c.png)

_Valid values accepted by QGIS_

![picture 25](images/0539a506650e623b7fbf8a77c0040e2177dab4a825054199fb0eaa325c4caf15.png)

_Polygons are displayed using the hexadecimal color contained in their `color` field_

#### Export the polygons to the GeoJSON format

Right click on your polgygons layer > Export

![picture 23](images/ff821c9533e2c183e75abb1797540f434b5bd715df6840c916b598b9a5f71fee.png)

_Export under the GeoJSON format_

:information_source: You can visualize the metadata under a table format by right clicking on the polygons layer > Open Attribute Table

You can also use the button from the navigation bar:

![picture 29](images/8095b735f64fb2ca9b67630730343d86000efb725495959f7a0806b6e55d9aa1.png)

:information_source: If for some reason you cannot create the GeoJSON file, an example file is provided here: `resources/solution/polygons.geojson`

## Python

### Introduction

#### Command line usage

:information_source: All commands assume that you `cd`ed into this project root folder.

The following commands will use bash. If you are a windows user with git installed, you can create a git bash shell from VSCode.

First, to satisfy the dependencies required by the project, run:

```bash
poetry install
```

To see the different arguments the script accept, run the following command from the project's root:

```bash
python ./training_raster_clipper/main.py -h
```

#### `launch.sh` script

You can use the `launch.sh` script and change it according to your needs so you don't have to type a long command, just:

```bash
./launch.sh
```

- TUTORIAL_STEP: Corresponds to the step in the code we want to reach. Use this during the tutorial to make the script work until the intended step.
- POLYGONS_INPUT_PATH: The GeoJSON polygons exported from QGIS
- RASTER_INPUT_PATH: The location of the `.SAFE` file containing the Sentinel-2 product
- CSV_OUTPUT_PATH: A CSV file of classified pixels of the Sentinel-2 product
- RASTER_OUTPUT_PATH: A raster resulting from the `sklearn` classification

#### Write your own code

Along the tutorial, you will have to write implementations of the functions provided in `implementation/your_work.py`. Each numbered sub-section corresponds to a function.

Before starting, you can have a glimpse of what the final result will look like by using the cheat flag (`-c`). It will use the solution implementations of the functions from `implementation/solutions.py`. Remove this flag when you start coding!

#### High-level process

Below is a diagram representing the data flow, from your two inputs (the Sentinel-2 product and a GeoJSON file containing multipolygons), up to the final result: the classified Sentinel-2 product

![picture 11](images/c176acb489c87139b438be9f3e50d922a3f3ff9c186c224ccb6818dd6899a043.png)

### (1) Load a GeoJSON file with `geopanda`

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

### (2) Load a Sentinel-2 raster with `rioxarray`

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

### (3) Rasterize the polygons

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

### (4) Intersect the Sentinel-2 raster with polygons

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

### (5) Persist the intersection to a CSV

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

### (6) Train a machine learning model

:information_source: For more details about the theoretical background of this section, you can ask Pierre Louvart

```python
def classify_sentinel_data(
    rasters: xr.DataArray,
    classified_rgb_rows: ClassifiedSamples
) -> np.ndarray:
```

We will now use the tools provided by `scikit-learn` to classify the rest of the pixels of the Sentinel rasters.

:arrow_forward: Instantiate a [`RandomForestClassifier`](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html)

:arrow_forward: Extract the training input samples from the `classified_rgb_rows`: they are all the columns except the last one from

:arrow_forward: Extract the class labels from the `classified_rgb_rows`: it is the last remaining column

:arrow_forward: Train the model using [`RandomForestClassifier.fit`](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html#sklearn.ensemble.RandomForestClassifier.fit)

:arrow_formard: Use the model to [`predict`](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html#sklearn.ensemble.RandomForestClassifier.predict) the classes of the rest of the Sentinel-2 raster, and return the result. The prediction needs a list of elements, with each element being a list of reflectances in all bands. See `reshape` from numpy. Remainder: `rasters.values` gives access to the underlying numpy array.

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

### (7) Export the classification raster result

```python
def persist_classification_to_raster(
    raster_output_path: Path, rasters: xr.DataArray, classification_result: np.ndarray
) -> None:
```

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

As done before, add a Raster layer using the output `.tiff` file generated from the python script. In the Symbology menu, choose Paletted/Unique values, then classify. It is left to the reader to display the raster using the already defined colors from the GeoJSON file!

![picture 30](images/f720e4418255c43d4680cea447b980faea67f48b44d63ce3bc7a04f5936baef5.png)

## Feedback

If you have any questions or feedback regarding this tutorial, please contact me (Etienne) or Pierre

## Improvements ideas

- You can add another step to persist the model, so it can be computed once and then reused on other images, rather than recalculating it on each script execution

## Tout Doux

- [ ] eschalk export palette with python and auto import in QGIS
- [ ] eschalk show the legend for classes
- [x] eschalk add title to plot
- [x] eschalk improve logging
- [x] eschalk create a helper imshow function
- [x] eschalk Create on the QGIS part a color field as well as the class field
