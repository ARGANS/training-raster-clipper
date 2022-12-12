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

TODO export palette with python and auto import in QGIS

## QGIS (departure)

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

[TODO eschalk]

## Python

### Load a Sentinel-2 raster (`rioxarray`)

```python
def load_sentinel_data(
    sentinel_product_location: Path,
    *,
    resolution: Optional[Literal[60] | Literal[20] | Literal[10]] = 60,
) -> xr.DataArray:
```

[TODO eschalk]

### Load a GeoJSON file (`geopanda`)

```python
def load_feature_polygons(input_path: Path) -> GeoDataFrame:
```

[TODO eschalk]

### Rasterize the polygons

```python
def rasterize_geojson(
    data_array: xr.DataArray,
    training_classes: GeoDataFrame,
) -> Tuple[PolygonMask, Mapping]:
```

[TODO eschalk]

### Intersect the Sentinel-2 raster with polygons

```python
def produce_clips(
    data_array: xr.DataArray, burnt_polygons: PolygonMask, mapping: Mapping
) -> ClassifiedSamples:
```

[TODO eschalk]

### Persist the intersection to a CSV

```python
def persist_to_csv(
    classified_rgb_rows: ClassifiedSamples,
    csv_output_path: Path,
) -> None:
```

[TODO eschalk]

### Train a machine learning model

```python
def classify_sentinel_data(
    rasters: xr.DataArray,
    classified_rgb_rows: ClassifiedSamples
) -> np.ndarray:
```

[TODO eschalk]

### Add the NIR band to get better results

The goal of this part is to show that using the NIR (Near-Infrared) band can help identify water and provide better classification results. The subsidiary goal is to show that with a flexible enough code, loading this NIR band should be as simple as adding a new value in the `Color` enum.

[TODO eschalk]

### Export the classification raster result

```python
def persist_classification_to_raster(
    raster_output_path: Path, rasters: xr.DataArray, classification_result: np.ndarray
) -> None:
```

[TODO eschalk]

## QGIS (arrival)

### Import the classification raster result
