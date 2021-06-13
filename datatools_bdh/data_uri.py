import io, base64

# --- local imports in functions
# import matplotlib.pyplot as plt

def bytes_to_uri(data, imgtype='jpeg', mimeprefix='image'):
    """ Create a data: URI using base64.b64encode() on the given `data`.
    
    Parameters:
        data - object of type io.BytesIO or Python bytes
        imgtype - image type in image/... mime type, e.g. jpeg or png
        mimeprefix - mime type prefix, default: image
    """
    try:
        data64 = base64.b64encode(data.getvalue())
    except AttributeError:
        data64 = base64.b64encode(data)
    return u'data:'+mimeprefix+'/'+imgtype+';base64,'+data64.decode('utf-8')

def savefig_uri(**kwargs):
    """Save current figure into data URI.
       Example: savefig_uri(format='png', transparent=True)
    """
    import matplotlib.pyplot as plt
    buf = io.BytesIO()
    plt.savefig(buf, **kwargs)
    buf.seek(0)
    return bytes_to_uri(buf)
