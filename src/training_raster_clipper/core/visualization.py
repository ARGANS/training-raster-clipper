import numpy as np
import numpy.typing as npt
import xarray as xr
from geopandas.geodataframe import GeoDataFrame
import matplotlib.pyplot as plt


def plot_rgb_data_array(xds: xr.DataArray, title: str):
    plt.figure()

    ax = xds.sel(band=["B04", "B03", "B02"]).plot.imshow(vmax=np.percentile(xds, 95))
    ax.axes.set_aspect("equal")
    ax.axes.set_title(title)


def plot_array(array: npt.NDArray[np.uint8] | xr.DataArray, title: str):
    plt.figure()

    ax = plt.imshow(array)
    ax.axes.set_aspect("equal")
    ax.axes.set_title(title)


def plot_geodataframe(gdf: GeoDataFrame, title: str):
    ax = gdf.plot(legend=True, color=gdf["color"])
    ax.axes.set_aspect("equal")
    ax.axes.set_title(title)
