""" Tools to work with Statistics Canada's Postal code conversion file
"""

from datatools_bdh import _get_resource_path
import pandas as pd

rldf = None
pccf_df = None

def init_pccf(filename):
    """Load the raw 2020 Postal code conversion file from given `filename`
       Call this with the location of pccfNat_fccpNat_082020.txt
    """
    global pccf_df, rldf

    rldf = pd.read_csv(_get_resource_path('pccf_2020_record_layout.csv'))

    # load the raw text pccf file
    with open(filename,'r', encoding='latin-1') as fh:
        pctxt = fh.read()

    pclines = pctxt.split('\n')

    pclines = list(filter(lambda l: len(l), pclines)) # keep only non-empty lines
    pcs = pd.Series(pclines)

    def gen_pccf():
        for idx, r in rldf.iterrows():
            yield r['Field name'], pcs.str[r['Position']-1:r['Position']+r['Size']-1]
            
    pccf_df = pd.DataFrame(dict(gen_pccf()))

    # remove whitespace around string fields
    pccf_df["Comm_Name"] = pccf_df["Comm_Name"].str.strip()
    pccf_df["Community"] = pccf_df["Comm_Name"].str.replace("-"," ").str.title()
    pccf_df["CSDname"] = pccf_df["CSDname"].str.strip()
    # lat/lon as floating point (N type in record layout)
    pccf_df["LAT"] = pccf_df["LAT"].astype(float)
    pccf_df["LONG"] = pccf_df["LONG"].astype(float)
