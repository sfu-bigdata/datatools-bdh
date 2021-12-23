"""Pandas utilities for DataFrames, Series, etc. """

import pandas as pd
import numpy as np
from bisect import bisect_left
import datetime
import os
import re

from .utils import gen_filename
from .data_uri import bytes_to_uri
from .ipython import HTML

# ---------------------------------------------------------------------------

def tabulate_list(lst):
    """Show list content as unescaped HTML table."""
    return HTML(
        pd.DataFrame(lst)
         .style
         .hide_index()
         .set_table_styles([{'selector': 'thead', 
                             'props': [('display', 'none')]}])
         .render(escape=False))

def markdown_to_html(non_p_string) -> str:
    ''' Strip enclosing paragraph marks, <p> ... </p>, 
        which markdown() forces, and which interfere with some jinja2 layout
    '''
    from markdown import markdown as markdown_to_html_with_p
    return re.sub("(^<P>|</P>$)", "", markdown_to_html_with_p(non_p_string), flags=re.IGNORECASE)

# ---------------------------------------------------------------------------
# dataframe to SVG conversion via command line tools

def make_table_html(df, title=''):
    '''
    Write an entire dataframe to an HTML string with nice formatting.
    '''

    result = '''
<html>
<head>
<style>
    h2 {
        text-align: center;
        font-family: sans-serif;
    }
    table { 
        margin-left: auto;
        margin-right: auto;
    }
    table, th, td {
        #font-family: sans-serif;
        #border: 1px solid black;
        #border-collapse: collapse;
    }
    th, td {
        text-align: left;
        font-family: monospace;
        font-size:10;
        padding: 0 2px;
    thead tr {
        font-family: sans-serif;
        text-align: center;
    }
    .wide {
        width: 90%; 
    }

</style>
</head>
<body>
    '''
    #-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Oxygen-Sans,Ubuntu,Cantarell,"Helvetica Neue", sans-serif
    result += '<h2> %s </h2>' % title
    if type(df) == pd.io.formats.style.Styler:
        result += df.render()
    else:
        result += df.to_html(classes='wide', escape=False)
    result += '''
</body>
</html>
'''
    return result

def write_to_html_file(df_sl, filename='out.html'):
    result = make_table_html(df_sl)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(result)

def make_df_svg_uri(df_sl, fnhead, show_errors=False,
                    do_remove_files=True,
                    do_optimize_svg=False):
    """Display a dataframe as formatted HTML and capture as SVG in URI form.
    The URI can be used in an <img> tag to display the dataframe as SVG.
    """
    fnbase = f"{fnhead}_{gen_filename()}"
    outfile = f'{fnbase}.html'
    pdffile = f'{fnbase}.pdf'
    svgfile = f'{fnbase}.svg'
    write_to_html_file(df_sl, filename=outfile)
    #--disable-smart-shrinking 
    # --page-width 8in --page-height 11in\
    if show_errors:
        debug_err = ''
        debug_std = ''
    else:
        debug_err = '2> /dev/null'
        debug_std = '> /dev/null'

    os.system(f"wkhtmltopdf --dpi 120 -T 0 -B 0 -L 0 -R 0 --encoding utf-8 --custom-header 'meta' 'charset=utf-8' "
              f"{outfile} {pdffile} {debug_err}")
    os.system(f"pdfcrop {pdffile} {debug_std}")
    #os.system(f"inkscape -l {svgfile} --export-area-drawing --vacuum-defs {pdffile}")
    os.system(f"inkscape {pdffile.replace('.pdf','-crop.pdf')} --vacuum-defs --export-filename={svgfile} {debug_err}")
    #os.system(f"inkscape {pdffile} --vacuum-defs --export-filename={svgfile} {debug_err}")
    # os.system(f"pdf2svg {pdffile.replace('.pdf','-crop.pdf')} {svgfile}")
    # os.system("sleep .5")
    if do_optimize_svg:
        os.system(f"svgo {svgfile} {debug_std}")
    dat_uri = bytes_to_uri(open(svgfile,'rb').read(), imgtype='svg+xml')
    if do_remove_files:
        os.system(f"rm -f {fnbase}*")
    return dat_uri

def dataframe_svg_html(df_sl, width="90%"):
    dat_uri = make_df_svg_uri(df_sl, fnhead='sl_table')
    return HTML(f"<img src='{dat_uri}' width={width}/>")

def hide_repeated_cells(x):
    """Hide values that are the same as the row above"""
    c1='visibility:hidden'
    c2=''
    cond = x.iloc[:-1,:].values == x.iloc[1:,:].values
    cr = cond[0].copy()
    cr[:] = False
    cond = np.vstack([cr,cond])
    df1 = pd.DataFrame(np.where(cond,c1,c2),columns=x.columns,index=x.index)
    return df1

#----------------------------------------------------------------------------

def index_columns(df, none_name=None):
    """Return list of column names that form the (multi-)index or None, if index is a single unnamed
    column."""
    try:
        return [l.name for l in df.index.levels]
    except AttributeError:
        name = df.index.name
        if name is not None:
            return [name]
        elif none_name is not None:
            return [none_name]


def split_by_index(df, split_idx):
    """
    Split DataFrame df at or around the given index value

    :param df: DataFrame with a sorted index
    :type df: pandas.DataFrame

    :param split_idx: The index value to split df by.
    :type split_idx: int

    :return: - **low_df** (`pandas.DataFrame`) - DataFrame containing index values below split_idx
             - **high_df** (`pandas.DataFrame`) - DataFrame containing index values greater than or
               equal to split_idx.
    """
    try:
        idx = df.index.get_loc(split_idx)
    except KeyError:
        idx = bisect_left(df.index, split_idx)
    return df.iloc[:idx, :], df.iloc[idx:, :]


def update_on(df, dfu, on=None):
    """Use DataFrame.update() function inplace, matching on any set of columns."""
    if on:
        inames = index_columns(df)
        uinames = index_columns(dfu)
        df.reset_index(inplace=True)
        df.set_index(on, inplace=True)
        if uinames is not None:
            df.update(dfu.reset_index().set_index(on))
        else:
            # id dfu index is unnamed, drop it to avoid collision with df index
            df.update(dfu.set_index(on))
        if inames is None:
            df.reset_index(inplace=True)
            df.set_index('index', inplace=True)
            df.index.name = None
        else:
            df.reset_index(inplace=True)
            df.set_index('index', inplace=True)
    else:
        df.update(dfu)


def dataframe_schema(columns, dtypes):
    """Create empty pd.DataFrame with columns of given datatypes"""
    df_dict = {cname: pd.Series([], dtype=dtype) for cname, dtype in zip(columns, dtypes)}
    return pd.DataFrame(df_dict)


def remove_microsecond(ts):
    return pd.Timestamp(year=ts.year, month=ts.month, day=ts.day, hour=ts.hour, second=ts.second)


def get_next_index(df, index_val, lock_bound=False, inc=+1):
    """Determine the index value that follows `index_val`

    :param df: dataframe or series, having df.index.
    :type df: pd.DataFrame or pd.Series

    :param index_val:  index value to start from

    :param lock_bound: if true return same index if reaching bounds
    :type lock_bound: bool

    :param inc: Increment. default +1, use -1 to get previous index
    :type inc: int

    :return: neighbouring index value
    """
    index_value_iloc = df.index.get_loc(index_val)
    next_iloc = index_value_iloc + inc
    try:
        next_index_value = df.index[next_iloc]
    except IndexError:
        if lock_bound:
            return index_value_iloc
        else:
            next_index_value = None

    return next_index_value

# ---------------------------------------------------------------------------

def value_counts_weighted(df, fields, weight_name='weight', count_name=None, ascending=None):
    """Replacement for pandas DataFrame.value_counts() summing the column given in `weight_name`.
       To obtain raw counts, as provided by original value_counts, use a column with contant 1.
       Args:
           df          - dataframe to perform value counts for
           fields      - fields whose values should be counted
           weight_name - name of weight column
           count_name  - name for resulting field containing counts (default: 'count')
           ascending   - True/False for sorting order, None to keep original order (default)
        Returns:
            pandas Series of counts
    """
    vc_df = df.groupby(fields)[weight_name].sum()
    if ascending is None:
        pass
    elif isinstance(fields, str):
        vc_df = vc_df.sort_values(ascending=ascending).rename()
        if count_name is None:
            count_name = fields
            vc_df.index.name = None
    else:
        # If multiple fields are use, vc_df is going to have a multi-index.
        # Construct a multi-index that produces the sorted order from first to last field
        # TODO: check this implementation or remove it
        def gen_all():
            for field in fields:
                yield value_counts_weighted(df, field).sort_values(ascending=ascending).index
        vc_df = vc_df.loc[tuple(list(gen_all()))]
    if not count_name is None:
        vc_df = vc_df.rename(count_name)
    return vc_df

def make_weekday_df(start_date, end_date):
    """Make a pandas dataframe of weekday names for dates.
    The 'date' column is a string formatted as, e.g. 2019/07/25,
    the 'day' column is the full weekday name, lower case (sunday, monday, ...)
    """
    delta = datetime.timedelta(days=1)
    day = []
    date = []
    while start_date <= end_date:
        day.append(start_date.strftime('%A').lower())
        date.append(str(start_date).replace("-","/"))
        start_date+= delta
    df_weekday = pd.DataFrame()
    df_weekday['date'] = date
    df_weekday['day'] = day
    df_weekday['is_weekend'] = df_weekday['day'].isin(['sunday','saturday'])
    return df_weekday

def make_month_start_end_dates(month, year=2019):
    start_date = datetime.date(year, int(month), 1)
    end_date = (start_date  + pd.offsets.DateOffset(months=1, days=-1)).date()
    return start_date, end_date
