"""Signal-Bot Version"""

VERSION_TUPLE = (0, 2, 2)
VERSION = '.'.join(map(str, VERSION_TUPLE))
__version__ = VERSION

__all__ = ['VERSION_TUPLE', 'VERSION', '__version__']