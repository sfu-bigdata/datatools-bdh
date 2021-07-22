import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import warnings
from .data_uri import bytes_to_uri
from .ipython import render_uri
import io

def get_axis_bounds(ax=None):
    """Obtain bounds of axis in format compatible with ipyleaflet
    Returns:
        bounds np.array with lat and lon bounds.
        bounds.tolist() gives [[s, w],[n, e]]
    """
    if ax is None:
        ax = plt.gca()
    return np.array([ax.get_ylim(), ax.get_xlim()]).T

def translate_latlon_bounds(fig_bounds, lon_shift=.9, lat_scale=.7):
    """Generate bounds for a colorbar to place next to a figure overlay.
       This is a utility function for ipyleaflet.
    """
    cbar_fig_bounds = fig_bounds.copy()
    cbar_width = cbar_fig_bounds[:,1] @ [-1,1]
    nb = cbar_fig_bounds[:,1] + cbar_width * lon_shift
    cbar_height = cbar_fig_bounds[:,0] @ [-1,1]
    cbar_fig_bounds[:,1] = nb
    cbar_fig_bounds[0,0] = cbar_fig_bounds[1,0] - cbar_height * lat_scale
    return cbar_fig_bounds

def set_font(size, family='sans-serif', weight='normal'):
    """Set the global font for matplotlib"""
    font = {'family' : family,
            'weight' : weight,
            'size'   : size}
    mpl.rc('font', **font)

def set_xticklabels_nowarn(ax, xticks=None, autoscale=1000, suffix="k"):
    """Adjust xticklabels to abbreviated multiples of 1000 (or value of autoscale)"""
    if xticks is None:
        xticks = pd.Series(ax.get_xticks()/autoscale).astype(int).astype(str) + suffix
    with warnings.catch_warnings(record=True) as w:
        ax.set_xticklabels(xticks)

def savefig_uri(**kwargs):
    """Save current figure into data URI.
       Example: savefig_uri(format='png', transparent=True)
    """
    f = lambda buf: plt.savefig(buf, **kwargs)
    return render_uri(f, format=kwargs.get('format', 'png'))
