""" IPython/Jupyter tools
"""

from IPython.display import display, Markdown
from IPython.core.magic import register_line_magic

def displaymd(strmd):
    """Display Markdown in notebook"""
    display(Markdown(strmd))

@register_line_magic
def markdown(line):
    """ %markdown line magic to display formatted markdown within a Python cell

    Examples:
    %markdown ## City: Burnaby
    %markdown { f"Number of 6-digit postal codes: {burnaby_pcs.size}" }
    """
    displaymd(line)
del markdown


def display_full_df(df, max_rows=None, max_columns=None):
    import pandas as pd
    with pd.option_context('display.max_rows', max_rows,
                           'display.max_columns', max_columns,
                           'display.max_colwidth', -1):
        display(df)

# TODO: Sort out the following buggy behaviour
#
# `%markdown {f"hello {42}"}``
# Should result in:
# hello 42
# However, it produces:
# {f"hello {42}"}
# This means that the f-string is not properly parsed, which is often an indication of an error raised 
# when processing the string. However, there is no message sharing any details on what went wrong.
#
# A workaround is to insert a : into the portion of the string 
# preceeding the { code } block:
# `%markdown {f"hello: {42}"}`
# Produces correct output:
# hello: 42
#
# Current guess is that the problem is upstream from def markdown(line) in a place where the 
# string for `line` is constructed during processing of the one-line magic input in IPython.
