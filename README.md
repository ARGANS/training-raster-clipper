# training-raster-clipper

## Sentinel-2 Product Structure

See official documentation: 
https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-2-msi/data-formats

Structure of an example product downloaded from https://scihub.copernicus.eu/dhus/#/home

```
tree d:\Profils\eschalk\Downloads\S2A_MSIL2A_20221116T105321_N0400_R051_T31TCJ_20221116T170958\S2A_MSIL2A_20221116T105321_N0400_R051_T31TCJ_20221116T170958.SAFE
Folder PATH listing for volume DATA
Volume serial number is 00310032 1ABB:1EC4
D:\PROFILS\ESCHALK\DOWNLOADS\S2A_MSIL2A_20221116T105321_N0400_R051_T31TCJ_20221116T170958\S2A_MSIL2A_20221116T105321_N0400_R051_T31TCJ_20221116T170958.SAFE
├───AUX_DATA
├───DATASTRIP
│   └───DS_ATOS_20221116T170958_S20221116T105603
│       └───QI_DATA
├───GRANULE
│   └───L2A_T31TCJ_A038658_20221116T105603
│       ├───AUX_DATA
│       ├───IMG_DATA
│       │   ├───R10m
│       │   ├───R20m
│       │   └───R60m
│       └───QI_DATA
├───HTML
└───rep_info
```

## Opening Raster 

See [Adding band description to rioxarray to_raster()](https://stackoverflow.com/questions/65616979/adding-band-description-to-rioxarray-to-raster)

## Error fixes

TypeError: GDAL-style transforms have been deprecated: https://gis.stackexchange.com/questions/403148/type-error-for-gdal-gdal-style-transforms-have-been-deprecated

## Examples of selection 

```python
(Pdb)  xds.sel(band=Color.RED.value)                  
<xarray.DataArray (y: 1830, x: 1830)>
array([[0.172 , 0.1677, 0.1614, ..., 0.1329, 0.1313, 0.1291],
       [0.171 , 0.1666, 0.1674, ..., 0.1315, 0.1296, 0.1329],
       [0.1797, 0.1531, 0.1551, ..., 0.1305, 0.1296, 0.1344],
       ...,
       [0.1353, 0.1321, 0.1216, ..., 0.1713, 0.1412, 0.1603],
       [0.116 , 0.1325, 0.1314, ..., 0.2727, 0.263 , 0.208 ],
       [0.1248, 0.1357, 0.1402, ..., 0.2427, 0.233 , 0.248 ]])
Coordinates:
    band         <U3 'B04'
  * x            (x) float64 3e+05 3.001e+05 3.002e+05 ... 4.097e+05 4.098e+05
  * y            (y) float64 4.9e+06 4.9e+06 4.9e+06 ... 4.79e+06 4.79e+06
    spatial_ref  int32 0
Attributes:
    scale_factor:  1.0
    add_offset:    0.0
(Pdb)  xds.sel(band=Color.RED.value)[[0, 1], [0, 1]]   
<xarray.DataArray (y: 2, x: 2)>
array([[0.172 , 0.1677],
       [0.171 , 0.1666]])
Coordinates:
    band         <U3 'B04'
  * x            (x) float64 3e+05 3.001e+05
  * y            (y) float64 4.9e+06 4.9e+06
    spatial_ref  int32 0
Attributes:
    scale_factor:  1.0
    add_offset:    0.0
```

## Drafts


```python
    xds = merge_arrays(
        [rioxarray.open_rasterio(band_file_paths[color]) for color in Color]
        [f(x) for in [1,2,3]]
        [f for in [1,2,3]]
        map(     f, [], )
    )
    args = []
    kwargs = {}
    f(*args, **kwargs)
    d1,d2
    d = {**d1, **d2}
    f = lambda (x,y) : x+y
    f(*(1,2))
```

```python
    info(xds.sel(band="B02"))  # selects the dimension
    info(xds.sel(band=["B02"]))  # keeps the englobing structure
    info(xds.sel(band=["B02", "B04"]))

    # https://corteva.github.io/rioxarray/stable/examples/clip_geom.html#Clip-using-a-geometry
    # https://corteva.github.io/rioxarray/stable/examples/clip_geom.html#Clip-using-a-GeoDataFrame

    # https://rasterio.readthedocs.io/en/latest/topics/masking-by-shapefile.html
    # https://www.earthdatascience.org/courses/use-data-open-source-python/intro-vector-data-python/vector-data-processing/clip-vector-data-in-python-geopandas-shapely/
    # https://spatial-dev.guru/2022/09/15/clip-raster-by-polygon-geometry-in-python-using-rioxarray/

    # https://corteva.github.io/rioxarray/html/rioxarray.html#rioxarray.raster_array.RasterArray
    # https://corteva.github.io/rioxarray/html/rioxarray.html#rioxarray.raster_array.RasterArray.clip

        # clipped, out_transform = mask(xds, gdf.geometry.values, invert=False)
    # https://gis.stackexchange.com/questions/401347/masking-raster-with-a-multipolygon

    # out_image, out_transform = rasterio.mask.mask(src, geo.geometry, filled = True)
    # out_image.plot()
    # # TODO eschalk flatten the mono-multipolygons to polygons before clipping as multipolygons are not supported
    # cropped = xds.rio.clip(geometries=gdf.geometry.values[0], crs=32631)

    # # cropped = xds.rio.clip(geometries=gdf.geometry.values[0], crs=4326)
    # clipped = cropped

    # info(clipped)

    # clipped.plot()

    # TODO eschalk
    # plt.show()
```
