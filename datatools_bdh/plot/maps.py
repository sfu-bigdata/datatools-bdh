"""Custom drawing functions for maps"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import tri
import math

try:
    # basemap related, tolerate if these imports are missing
    import geopandas
    from PIL import Image as PILImage
except ModuleNotFoundError:
    pass

from ..utils import extend_range, isnumber
from .colormaps import alpha_from_max

# ---------------------------------------------------------------------------
# generic geospatial utils

def euclidean(lon1, lat1, lon2, lat2):
    "Calculate euclidan distance between two points in km"
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    # radius of earth in kilometers is 6371
    km = 6371 * c
    return float(km)

def get_aspect_latlon(lalo):
    """Compute aspect ratio of y/x for given lat/lon position in `lalo` tuple."""
    km_lat = euclidean(*lalo, *lalo+[1,0]) # y is latitude, on axis 0
    km_lon = euclidean(*lalo, *lalo+[0,1]) # x is longitude, on axis 1
    return km_lat / km_lon

# ---------------------------------------------------------------------------
# static basemap rendering

def add_basemap(extent_wesn=None, zoom='auto', source='none', 
                ax=None, zorder=100, alpha_tf=alpha_from_max, extend_ratio=.1, **kwargs):
    """Add a basemap with selective transparency to place on top of existing figure.
    Args:
        extent_wesn - Extent in lat/lon (west, east, south, north),
                      If None, will use (*ax.xlim(), *ax.ylim()).
                      If float, will be have like None and extend (buffer) axis range by given ratio.
        zoom - zoom level for contextily.bounds2img (default: 'auto'), int between 0 - 20
        source - tile provider for contextily.bounds2img, 
                 default: contextily.providers.Stamen.TonerLite
        ax - axis to plot basemap into, possibly with pre-existing rendering
        zorder - composition z-order for drawing on top or below existing figure content
                 (default: 100)
        alpha_tf - alpha value transform (default: alpha_from_max)
        **kwargs - further named arguments passed on to matplotlib.pyplot.imshow
    Returns:
        AxesImage output of matplotlib.pyplot.imshow
    """
    import contextily
    if source == 'none':
        source = contextily.providers.Stamen.TonerLite
    auto_extent = extent_wesn is None or isnumber(extent_wesn)
    if ax is None:
        ax = plt.gca()
    if auto_extent:
        extend_ratio = extent_wesn if isnumber(extent_wesn) else 0
        extent_wesn = (*extend_range(ax.get_xlim(), extend_ratio),
                       *extend_range(ax.get_ylim(), extend_ratio))
    extent_wsen = np.array(extent_wesn)[[0,2,1,3]]

    image, bounds = contextily.bounds2img(*extent_wsen, zoom=zoom, ll=True, source=source)

    bbi = PILImage.fromarray(image).convert('RGBA')
    bbd = np.array(bbi.getdata(), dtype=int)
    bbd = alpha_tf(bbd)
    bbi.putdata(list(map(tuple, bbd)))

    bounds = np.array(bounds)
    bounds_ll = np.array(geopandas.GeoSeries(geopandas.points_from_xy(bounds[[0,1]], bounds[[2,3]],crs=3857),
                           ).to_crs(4326).apply(lambda p: list(p.coords[0])).sum())
    g = ax.imshow(bbi, extent=bounds_ll[[0,2,1,3]], zorder=zorder, **kwargs)
    
    return g

# ---------------------------------------------------------------------------
# 

DEFAULT_TRI_FILTER_K = 5*1e-3

def dist(x1, y1, x2, y2):
    """Euclidean distance between two points"""
    return math.sqrt((x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2))

def is_triangle_too_big(x, y, k=DEFAULT_TRI_FILTER_K):
    """Compare length of triangle edges against threshold `k`.
       Triangle corners x and y coordinates are given in arrays `x` and `y`, respectively.
    """
    return (dist(x[0], y[0], x[1], y[1]) > k) or (dist(x[0], y[0], x[2], y[2]) > k) or (dist(x[2], y[2], x[1], y[1]) > k)

def filter_triangles(x, y, k=DEFAULT_TRI_FILTER_K):
    """Perform is_triangle_too_big() check on each triangle given in arrays `x` and `y`."""
    results = []
    for i in range(x.shape[0]):
        results.append(is_triangle_too_big(x[i], y[i], k))
    return np.array(results)

def plot_tripcolor(df, field_name, cmap="rocket", filter_triangles_k=None, ax=None, **kwargs):
    """Use matplotlib.pyplot.tripcolor to visualize scalar quantity on a map.
    """
    if ax is None:
        plt.figure(); ax = plt.axes([0,0,1,1])

    x = df["LONG"].to_numpy()
    y = df["LAT"].to_numpy()

    z = df[field_name].fillna(0).to_numpy()

    triang = tri.Triangulation(x, y)

    if not filter_triangles_k is None:
        k = filter_triangles_k if isnumber(filter_triangles_k) else DEFAULT_TRI_FILTER_K
        triang.set_mask(filter_triangles(x[triang.triangles], y[triang.triangles]))
    g = ax.tripcolor(triang, z, alpha=.8, shading='flat', edgecolor=None, linewidth=0, cmap=cmap, antialiased=True, **kwargs)
#    plt.axis('off')

    return g
