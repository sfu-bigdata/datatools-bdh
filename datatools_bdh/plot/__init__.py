import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

import warnings
from ..ipython import render_uri, render_bytes, display
from .maps import *

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

# ---------------------------------------------------------------------------
# Generic utility functions

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

@mpl.ticker.FuncFormatter
def thousands_k_fmt(x, pos):
    return f"{x/1000:,.0f}k"

@mpl.ticker.FuncFormatter
def percent_fmt(x, pos):
    return f"{x*100:.0f}%"

def savefig_to_buffer(fig, **kwargs):
    return render_bytes(lambda buf: fig.savefig(buf, **kwargs))

def savefig_uri(**kwargs):
    """Save current figure into data URI.
       Example: savefig_uri(format='png', transparent=True)
       See also: render_uri()
    """
    plt_savefig = lambda buf: plt.savefig(buf, **kwargs)
    return render_uri(plt_savefig, format=kwargs.get('format', 'png'))

def set_plot_frame_visible(onoff=True):
    ax = plt.gca()
    ax.spines["top"].set_visible(onoff)
    ax.spines["right"].set_visible(onoff)
    ax.spines["bottom"].set_visible(onoff)
    ax.spines["left"].set_visible(onoff)

# ---------------------------------------------------------------------------
# table-table-correspondence matrix rendering

def make_grid(ax, ncols, nrows, nshrink_cr=None):
    """Draw a grid for given number of columns and rows.
    The grid lines are placed at the center of the cells of an
    adjacent table view.

    To skip the outmost layer of grid lines, we make a grid with fewer lines and 
    shrink the axis that contains the grid.
    The source numbers of columns or rows to scale from are
    nshrink_cr[0]+ncols and nshrink_cr[1]+nrows, respectively.
    If nshrink_cr == (1, 1), the table bounding box is scaled down to
    exclude the single outmost grid lines in both column and row direction.
 
    Args:
        ax - axis to create grid in and adjust bounding box
        ncols - target number of columns, num. of x ticks of grid lines
        nrows - target number of rows, num. of y ticks of grid lines
        nshrink_cr - pair of numbers of columns and rows to shrink axis by
    """
    ax.set_xticks(np.arange(1,(ncols)*2,2))
    ax.set_xlim(0,(ncols)*2)
    ax.set_xticklabels([])
    ax.set_yticks(np.arange(1,(nrows)*2,2))
    ax.set_ylim(0,(nrows)*2)
    ax.set_yticklabels([])
    ax.grid(True)
    if nshrink_cr:    
        shrink_axis_bbox(ax, 
                        s_width=(ncols)/(ncols+nshrink_cr[0]),
                        s_height=(nrows)/(nrows+nshrink_cr[1]))

def shrink_axis_bbox(ax, s_width, s_height):
    """Scale axis to exclude cells in column or row direction
        Args:
        ax - axis
        s_width - scaling factor of axis bounding box width
        s_height - scaling factor along height
    """
    from matplotlib.transforms import Bbox
    bboxob = ax.get_position()
    bbox = np.array(bboxob)
    bw = [-1, 1] @ bbox # get bbox width and height as row difference
    ax.set_position(Bbox([bbox[0,:], 
                            bbox[0,:] + bw*[s_width, s_height]]))

def make_datatable(cells, colors,
                   columnlabels=None, rowlabels=None,
                   rot_90=False,
                   table_font_size=14,
                   ax=None):
    """Draw a table view using matplotlib axes table
    Args:
        cells - dataframe with cell content (uses cells.T if rot_90)
        colors - dataframe with color names
        columnlabels - names of columns
        rowlabels - names of rows
        rot_90 - if True, rotate by 90 degrees CW
        table_font_size - font size
        ax - axis (could be from pyplot.subplots)
    """
    if ax is None:
        ax = plt.gca()
    ax.axis('off')
    if rot_90:
        tabwcols = cells.T.values[:,::-1]
        if not columnlabels is None:
            tabwcols = np.hstack([tabwcols, 
                                  columnlabels.values.reshape(-1,1)])
            columnlabels = None
        cellInfo = dict(cellText=tabwcols,
                        cellColours=np.hstack([colors.T[:,::-1], 
                                                np.array(["w"]*cells.shape[1] #ncols instead of #*nrows
                                                            ).reshape(-1,1)]))
    else:
        cell_values = cells.values.tolist()
        cellInfo = dict(cellText=cell_values,
                        cellColours=colors)
    the_table = ax.table(**cellInfo,
                        cellLoc='center',
                        colLabels=columnlabels,
                        rowLabels=rowlabels,
                        bbox=[0,0,1,1])
    if rot_90:
        for cell in the_table._cells:
            the_table._cells[cell].get_text().set_rotation(-90) # -90 CCW is 90 CW
    the_table.set_fontsize(table_font_size)

def matrix_to_df(mat):
    """Convert 2D numpy array to melted dataframe with (row, col) multi-index"""
    return (pd.DataFrame(mat)
                    .reset_index() # 'index' is row number
                    .melt(id_vars='index') # also: 'variable' is column id
                    .rename(columns={'index':'row','variable':'column'})
                    .set_index(['row','column'])
                    )

def make_cells(columns, rows):
    """Make a dataframe of cell contents and a matrix of colors.
       Returned args can be used by `show_table_matrix`."""
    ncols = len(columns)
    nrows = len(rows)
    cell_text = np.array([[k]*ncols for k in rows]) #, ["3"]*ncols
    cells = pd.DataFrame(cell_text, columns=columns, index=rows)
    colors = np.tile(np.array('w', dtype=object),  (nrows,ncols))
    return cells, colors

def show_table_matrix(cells, colors=None,
                      cells2=None, colors2=None,
                      link_matrix=None,
                      table_font_size=32,
                      rot_45=True,
                      return_img=False):
    """Draw a view of two tables together with a row-row association matrix.
    """
    from matplotlib import tight_layout
    fig, axs = plt.subplots(2, 2, figsize=(12,12))
    plt.subplots_adjust(wspace=0, hspace=0)
    axs[1,0].axis('off') # lower-left off
    ax=axs[0,0] # top-left
    make_datatable(cells, colors,
                   columnlabels=cells.columns,
                   table_font_size=table_font_size,
                   ax=ax)
    ax=axs[1,1] # lower right, table view rotated by 90 deg CW
    make_datatable(cells2, colors2,
                   columnlabels=cells2.columns,
                   rot_90=True,
                   table_font_size=table_font_size,
                   ax=ax)
    ax=axs[0,1] # top right
    make_grid(ax,
              ncols=cells2.shape[0], # table below grid (bottom right in rot_45 view)
              nrows=cells.shape[0], # table left of grid (bottom left in rot_45 view)
              nshrink_cr=(1, 1) # shrink axis bbox to remove one extra row and column
              )
    try:
        assert link_matrix.shape == (cells.shape[0], cells2.shape[0])
        links = matrix_to_df(link_matrix)
        for row, col in links[links.values].index:
            rowcol = np.array(link_matrix.shape) - (row, col) - 1
            doty, dotx = 2*rowcol+1
            ax.plot(
                    [dotx, dotx, 0],
                    [0, doty, doty],
                    linewidth=2,
                    color='black'
                    )
    except AttributeError:
        pass

    renderer = tight_layout.get_renderer(fig)
    if return_img or rot_45:
        img = plt.imread(savefig_to_buffer(fig, format='png', bbox_inches='tight'),
                         format='png')
    if rot_45:
        plt.close()
        from scipy.ndimage import rotate
        plt.figure(figsize=(12,12))
        plt.imshow(np.clip(rotate(img, angle=45,
                           cval=1 # white background instead of grey outline
                           ), 0, 1))
        plt.axis('off')
    if return_img:
        return img

def set_bg_col(s):
    """Set background color in pandas dataframe style.
    See also: `display_color_column`"""
    return s.map('background-color: {:}'.format)

def display_color_column(hexcol):
    """Display a pandas series of color hexcode with corresponding cell background color"""
    display(hexcol.style.apply(set_bg_col, axis=1))

def make_cmap_df(cmap, hex=False):
    """
    Example:
    ```
    cmap = mpl.cm.get_cmap('Paired', 12)
    cmap_df = make_cmap_df(cmap, hex=True)
    hexcol = cmap_df[['color']]
    display_color_column(hexcol.T)
    ```
    """
    cmap_df = pd.DataFrame((list(c for c in cmap(i)) for i in range(cmap.N)), columns=list('RGBA'))
    if hex:
        cmap_df = cmap_df.assign(color=lambda x: x.apply(mpl.colors.rgb2hex, axis=1))
    return cmap_df
