# datatools-bdh

Utility and helper functions used at SFU's Big Data Hub

The modules in this package mostly provide additional helper functions to work with other comprehensive libraries or environments, such as Pandas or IPython.

## Content

|   |   |
|---|---|
| `ipython` | Utilities to work with IPython and some Pandas  |
| `pccf` | Working with Canadian postal codes via the Stats Can Postal code conversion file |
| `data_uri` | Generate Data URIs |
| `mdocx` | Generate .docx report using markdown |

## Installation

It is possible to install this package directly from its public github location:

`pip install git+https://github.com/sfu-bigdata/datatools-bdh`

Alternatively, one can clone the repo and install locally:
```
git clone https://github.com/sfu-bigdata/datatools-bdh/tree/main/datatools_bdh
cd datatools_bdh
pip install -e .
```
The `-e` option installs the module via symbolic links, so code changes during development propagate more easily.

## Usage
IPython utilities:
```
from datatools_bdh.ipython import *

% markdown This is *single-line* markdown content within a Python cell.
```

Postal code conversion file:
```
import datatools_bdh.pccf as pccf
pccf.init('...pccf.txt filename...')

# access the PCCF DataFrame:
pccf.df
```
