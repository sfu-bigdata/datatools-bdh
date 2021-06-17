import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import warnings

def get_axis_bounds(ax=None):
    """Obtain bounds of axis in format compatible with ipyleaflet"""
    if ax is None:
        ax = plt.gca()
    return np.array([ax.get_ylim(), ax.get_xlim()]).T

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
