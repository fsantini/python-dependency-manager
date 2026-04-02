"""Main module."""

from .config import PackageManagers
from .DependencyManager import DependencyManager
from .exceptions import *
from .utils import *
from .installers import install_package_version, install_package

VERSION = '0.0.14'
__version__ = VERSION
