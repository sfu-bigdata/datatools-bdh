""" Tools to work with Statistics Canada's Postal code conversion file (pccf)

To work with the pccf, first initialize:
import datatools_bdh.pccf as pccf

`pccf.init('../../files/pccfNat_fccpNat_082020.txt')`

The use the conversion dataframe either via:
`pccf.df`
or via
`pccf._pccf_df()`
"""

from datatools_bdh import _get_resource_path
import pandas as pd

_rldf = None
_pccf_df = None

def _pccf_df():
    return _pccf_df

def __getattr__(name):
    if name == 'rldf':
        return _rldf
    if name == 'df':
        return _pccf_df
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

def init(filename):
    """Load the raw 2020 Postal code conversion file from given `filename`
       Call this with the location of pccfNat_fccpNat_082020.txt
    """
    global _pccf_df, _rldf

    _rldf = pd.read_csv(_get_resource_path('pccf_2020_record_layout.csv'))

    # load the raw text pccf file
    with open(filename,'r', encoding='latin-1') as fh:
        pctxt = fh.read()

    pclines = pctxt.split('\n')

    pclines = list(filter(lambda l: len(l), pclines)) # keep only non-empty lines
    pcs = pd.Series(pclines)

    def gen_pccf():
        for idx, r in _rldf.iterrows():
            yield r['Field name'], pcs.str[r['Position']-1:r['Position']+r['Size']-1]
            
    _pccf_df = pd.DataFrame(dict(gen_pccf()))

    # remove whitespace around string fields
    _pccf_df["Comm_Name"] = _pccf_df["Comm_Name"].str.strip()
    _pccf_df["Community"] = _pccf_df["Comm_Name"].str.replace("-"," ").str.title()
    _pccf_df["CSDname"] = _pccf_df["CSDname"].str.strip()
    # lat/lon as floating point (N type in record layout)
    _pccf_df["LAT"] = _pccf_df["LAT"].astype(float)
    _pccf_df["LONG"] = _pccf_df["LONG"].astype(float)

def filter_pc(province_filter=None, keep_first_pc=True, drop_da0=True):
    """Remove items from PCCF data frame."""
    global _pccf_df
    if not province_filter is None:
        _pccf_df = _pccf_df.loc[_pccf_df['Postal code'].str[0] == province_filter]
    if drop_da0:
        _pccf_df = _pccf_df.loc[_pccf_df['DAuid'] != '00000000']
    if keep_first_pc:
        _pccf_df = _pccf_df.groupby('Postal code').first().reset_index()

def get_community_codes(community, field="DAuid"):
    """Get DA codes for given community or city.
    Args:
        community - city name
        field - "DAuid" or "Postal code" or "FSA"
    """
    return _pccf_df.loc[_pccf_df['Community'] == community, field].unique()
