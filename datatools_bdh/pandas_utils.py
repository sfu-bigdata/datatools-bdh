"""Pandas utilities for DataFrames, Series, etc. """

import pandas as pd
from bisect import bisect_left
import datetime

# ---------------------------------------------------------------------------

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
