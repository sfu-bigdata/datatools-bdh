
import os.path

_resource_path = os.path.join(os.path.split(__file__)[0], "resources")

def _get_resource_path(*resource):
    return os.path.join(_resource_path, *resource)
