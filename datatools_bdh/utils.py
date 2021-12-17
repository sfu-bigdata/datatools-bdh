"""Generic utility functions"""

import os
import subprocess
import sys
import importlib
import uuid

# ----------------------------------------------------------------------------
# file path management
# interact with shell (to get git info)

def eval_shell(cmdargs):
    """ Run command in shell and return string output.
        Input `cmdargs` is list of command and individual args."""
    return (subprocess.
            Popen(cmdargs,
                  stdout=subprocess.PIPE)
            .communicate()[0]
            .rstrip()
            .decode('utf-8')
            )

_repo_path = None

def repo_path():
    global _repo_path
    if not _repo_path:
        _repo_path = eval_shell('git rev-parse --show-toplevel'.split())
    return _repo_path

def repo_file_path(*fn, folder="data"):
    return os.path.join(repo_path(), folder, *fn)

def load_file(filename):
    """
    Loads and returns the contents of filename.

    :param filename: A string containing the filepath of the file to be loaded/
    :type filename: str

    :return: Contents of the loaded file.
    :rtype: str
    """
    with open(filename, "r") as fh:
        return fh.read()

def gen_filename():
    return str(uuid.uuid4().hex)

def gdown_bytes(id, quiet=True):
    """Download a publicly shared file on google drive into BytesIO. """
    import gdown
    import io
    buf = io.BytesIO()
    gdown.download(f"https://drive.google.com/uc?id={id}",
                buf,
                quiet=quiet)
    buf.seek(0)
    return buf

def gdown_str(id, quiet=True, encoding='utf-8'):
    """Download a publicly shared file on google drive into string object. """    
    return gdown_bytes(id, quiet).read().decode(encoding)

# ----------------------------------------------------------------------------

def extend_range(min_max, extend_ratio=.2):
    """Symmetrically extend the range given by the `min_max` pair.
       The new range will be 1 + `extend_ratio` larger than the original range.
    """
    mme = (min_max[1] - min_max[0]) * extend_ratio / 2
    return (min_max[0] - mme, min_max[1] + mme)

def isnumber(n):
    import numbers
    return isinstance(n, numbers.Number)

def isiterable(obj):
    """Check if object `obj` is iterable."""
    try:
        iter(obj)
        return True
    except TypeError:
        return False

def ensure_list(items, item_type=str):
    """Ensure that `items` is a list, i.e. create single-element list if needed.
       Args:
        items     - single item or list of items
        item_type - check if `items` are of this type (default: str). If yes,
                    insert into a list.
       Returns:
        List of item(s)
       Example:
        fields = "City"
        ensure_list(fields) + ["Province"] results in ["City", "Province"]
    """
    if isinstance(items, item_type) or not isiterable(items):
        return [items]
    else:
        return items

# ----------------------------------------------------------------------------
# module reloading

def reload_all(module_name):
    """Reload all modules that have `module_name` in their path."""
    def num_dots(st):
        return sum(l=='.' for l in st[0])
    def get_modules():
        for mn, mo in sys.modules.items():
            try:
                if mn[:2] == '__':
                    continue
                if module_name in mo.__file__:
                    yield mn, mo
            except:
                pass
    for mn, mo in sorted(get_modules(), key=num_dots, reverse=True):
        #print('import {}'.format(mn))
        importlib.reload(mo)

def add_sys_path(addpath):
    if addpath not in sys.path:
        sys.path.append(addpath)

