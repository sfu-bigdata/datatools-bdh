import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import warnings
from ..ipython import render_uri
from . import colormaps

# ---------------------------------------------------------------------------
# Utilites to work with figure/axis bounds

def get_axis_bounds(ax=None):
    """Obtain bounds of axis in format compatible with ipyleaflet
    Returns:
        bounds np.array with lat and lon bounds.
        bounds.tolist() gives [[s, w],[n, e]]
    """
    if ax is None:
        ax = plt.gca()
    return np.array([ax.get_ylim(), ax.get_xlim()]).T

def translate_latlon_bounds(fig_bounds, lon_shift=.9, lat_shift=.7, aspect=.7, scale=1):
    """Generate bounds for a colorbar or legend to place next to a figure overlay.

       This is a utility function for ipyleaflet that allows to produce a position for a 
       color bar relative to the original figure bounds.

       The resulting bounds are shifted by a ratio of `lon_shift` in horizontal longitude
       direction and by a ratio of `lat_shift` in vertical direction. Then vertical scaling
       by `aspect` is applied and isometric scaling by `scale`, both types of scaling 
       are performed around the center of the figure.

       Args:
           fig_bounds - [ [bottom or S,  left or W], 
                          [   top or N, right or E] ] - figure bounds in lat long
           lon_shift - horizontal shift as ratio of figure width
           lat_shift - vertical shift as ratio of figure height
           aspect - aspect ratio (original bounds are assumed to be for aspect=1)
           scale - isometric re-scaling
       Returns:
           Adjusted bounds in the same format as fig_bounds
    """
    # [ [bottom or S,  left or W], 
    #   [   top or N, right or E] ] = fig_bounds # [[s, w], [n, e]]
    cbar_fig_bounds = fig_bounds.copy()
    cbar_width = cbar_fig_bounds[:,1] @ [-1,1]
    nb = cbar_fig_bounds[:,1] + cbar_width * lon_shift
    cbar_fig_bounds[:,1] = nb
    cbar_height = cbar_fig_bounds[:,0] @ [-1,1]
    nb = cbar_fig_bounds[:,0] + cbar_height * lat_shift
    cbar_fig_bounds[:,0] = nb
#    cbar_fig_bounds[0,0] = cbar_fig_bounds[1,0] - cbar_height * aspect
    cbar_hw = cbar_fig_bounds.T @ [-1,1]
    cbar_hw[0] *= aspect
    cbar_c = cbar_fig_bounds.T @ [.5, .5]
    cbar_fig_bounds = np.array([cbar_c - scale * .5 * cbar_hw,
                                cbar_c + scale * .5 * cbar_hw])
    #cbar_fig_bounds[1,:] = cbar_fig_bounds[0,:] + cbar_hw * scale
    return cbar_fig_bounds

def set_font(size, family='sans-serif', weight='normal'):
    """Set the global font for matplotlib"""
    font = {'family' : family,
            'weight' : weight,
            'size'   : size}
    mpl.rc('font', **font)

# ---------------------------------------------------------------------------
# Generic utility functions

def set_xticklabels_nowarn(ax, xticks=None, autoscale=1000, suffix="k"):
    """Adjust xticklabels to abbreviated multiples of 1000 (or value of autoscale)"""
    if xticks is None:
        xticks = pd.Series(ax.get_xticks()/autoscale).astype(int).astype(str) + suffix
    with warnings.catch_warnings(record=True) as w:
        ax.set_xticklabels(xticks)

def savefig_uri(**kwargs):
    """Save current figure into data URI.
       Example: savefig_uri(format='png', transparent=True)
       See also: render_uri()
    """
    plt_savefig = lambda buf: plt.savefig(buf, **kwargs)
    return render_uri(plt_savefig, format=kwargs.get('format', 'png'))
