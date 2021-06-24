""" IPython/Jupyter tools
"""

from IPython.display import display, Markdown, HTML
from IPython.core.magic import register_line_magic
import tabulate
import io
from .data_uri import bytes_to_uri

def displaymd(strmd):
    """Display Markdown in notebook"""
    display(Markdown(strmd))

def render_bytes(f):
    """Call f(buf) and contruct a BytesIO buf object.
       Example: render_bytes(f=lambda buf: plt.savefig(buf))
    """
    buf = io.BytesIO()
    f(buf)
    buf.seek(0)
    return buf

def render_bytes_to_uri(buf, **kwargs):
    """Contruct a data URI for BytesIO buf object.
       Example: render_bytes_to_uri(f=lambda buf: plt.savefig(buf), format='png')
    """
    return bytes_to_uri(buf, imgtype=kwargs.get('format', 'png'))

def render_uri(f, **kwargs):
    """Call f(buf) and contruct a data URI for returned BytesIO buf object.
       Example: render_uri(f=lambda buf: plt.savefig(buf), format='png')
    """
    return render_bytes_to_uri(render_bytes(f), **kwargs)

def dataframe_to_bytes(df):
    """Render formatted dataframe HTML to png and return a BytesIO buffer"""
    import dataframe_image as dfi
    f = lambda buf: dfi.export(df, buf)
    return render_bytes(f)

def dataframe_to_pil_image(df):
    """Render formatted dataframe HTML to png and return as PIL Image"""
    from PIL import Image
    buf = dataframe_to_bytes(df)
    return Image.open(buf)

def image_to_bytes(dfi, format='PNG'):
    "PIL image dfi converted to bytes by saving as given format (default: PNG)."
    return render_bytes( lambda buf: dfi.save(buf, format=format) )

def bytes_to_ipy_image(buf, **kwargs):
    "Create IPython Image from Bytes array"
    from IPython.display import Image
    return Image(data=buf.getvalue(), **kwargs)

def pil_to_ipy_image(pil_image, **kwargs):
    "Create IPython Image from PIL Image"
    buf = image_to_bytes(pil_image)
    return bytes_to_ipy_image(buf, **kwargs)

def dataframe_to_ipy_image(df, f=None, **kwargs):
    """Create IPython Image from PIL Image.
    Args:
    df - dataframe to render
    f - operation to perform on PIL Image (e.g. f=lambda img: img.rotate(-90, expand=True))
    kwargs - arguments to IPython.display.Image, such as width and height for html display
    """
    pil_image = dataframe_to_pil_image(df)
    if not f is None:
        pil_image = f(pil_image)
    return pil_to_ipy_image(pil_image=pil_image, **kwargs)

def dataframe_uri(df):
    """Render formatted dataframe HTML to png and return as data URI"""
    return render_uri(dataframe_to_bytes(df))

def display_df_image(df):
    displaymd(f"![]({dataframe_uri(df)})")

def insert_pagebreak():
    """Insert a pagebreak that renders invisibly in HTML, but shows in PDF and 
    can be utilized in .docx generation"""
    display(HTML('<div style="page-break-after: always;"></div>'))

def insert_pagebreak_landscape():
    """Insert a landscape pagebreak that renders invisibly in HTML, 
    but shows in .docx generation"""
    display(HTML('<div style="page-break-landscape-after: always;"></div>'))

try:
    get_ipython # raise NameError if we're not in IPython

    @register_line_magic
    def markdown(line):
        """ %markdown line magic to display formatted markdown within a Python cell

        Examples:
        %markdown ## City: Burnaby
        %markdown { f"Number of 6-digit postal codes: {burnaby_pcs.size}" }
        """
        displaymd(line)
    del markdown

except NameError:
    pass

def display_full_df(df, max_rows=None, max_columns=None):
    import pandas as pd
    with pd.option_context('display.max_rows', max_rows,
                           'display.max_columns', max_columns,
                           'display.max_colwidth', -1):
        display(df)

# ---------------------------------------------------------------------------
# table display related

def tree_to_HTML(tree):
    import lxml.etree as et
    return HTML(et.tounicode(tree))

def xpath_set_attr(tree, xpath, attr, val):
    for el in tree.xpath(xpath):
        el.attrib[attr] = val

def html_to_tree(html):
    import lxml.etree as et
    tree = et.fromstring(html)
    return tree

def html_table_width(html, widths, table_width=None):
    import lxml.etree as et
    tree = html_to_tree(html)
    if not table_width is None:
        xpath_set_attr(tree,
                       xpath="/table",
                       attr='style',
                       val=f"width:'{table_width};",
                      )
    def make_widths(widths):
        for w in widths:
            if not w is None:
                yield f'<col span="1" style="width: {w};"/>'
            else:
                yield f'<col span="1" />'
    widths_xml = ("<colgroup>\n" + 
                  "\n".join(make_widths(widths)) + 
                  "</colgroup>")
    XML = widths_xml
    parser = et.XMLParser(remove_blank_text=True)
    tag = et.fromstring(XML, parser)
    for t in tree.xpath("/table"):
        t.insert(0, tag)
    return tree_to_HTML(tree)

def make_html_table(table):
    """Use python-tabulate to render table to HTML. 
        Elements with HTML code will be used directly, trusting that they are
        generated safely.
    """
    return tabulate.tabulate(table, tablefmt='unsafehtml')

from io import StringIO 
import sys

class Capturing(list):
    """Capture stdout and stderr as context manager.
    See: https://stackoverflow.com/a/16571630/15377900
    """
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        self._stderr = sys.stderr
        sys.stderr = self._stringioe = StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        self.extend(self._stringioe.getvalue().splitlines())
        sys.stdout = self._stdout
        sys.stderr = self._stderr
        del self._stringio    # free up some memory
        del self._stringioe


# TODO: Sort out the following buggy behaviour of the %markdown magic above
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
