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