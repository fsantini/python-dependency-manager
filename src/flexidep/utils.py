"""Utilities for the environment."""

import os
import sys
import urllib.request
import json
import importlib.metadata as metadata
import re
from urllib.error import HTTPError
from packaging import version

from tqdm import tqdm

class PackageDict(dict):
    def __init__(self):
        dict.__init__(self)

    def __getitem__(self, item):
        item = _pypi_canonical_name(item)
        return super(PackageDict, self).__getitem__(item)

    def __setitem__(self, key, value):
        key = _pypi_canonical_name(key)
        return super(PackageDict, self).__setitem__(key, value)

def is_conda_environment():
    """Check if the current environment is a conda environment."""
    return os.path.exists(os.path.join(sys.base_prefix, 'conda-meta'))

def _pypi_canonical_name(name):
    """Return the canonical name of a package on PyPI."""
    return re.sub(r"[-_.]+", "-", name).lower()

def is_frozen():
    """Check if the current environment is a frozen (pyinstaller) environment."""
    return getattr(sys, 'frozen', False)

def get_pypi_available_versions(package_name):
    """Return a list of available versions for a package on PyPI."""
    #print("Processing", package_name)
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        with urllib.request.urlopen(url, timeout=1) as response:
            data = json.load(response)
    except (HTTPError, json.JSONDecodeError, UnicodeDecodeError):
        return []
    releases = []
    for version_raw in data['releases'].keys():
        try:
            version_obj = version.Version(version_raw)
        except version.InvalidVersion:
            continue
        releases.append(version_obj)
    return sorted(releases, reverse=True) # return releases from latest to oldest

def get_installed_packages():
    """Return a dictionary of (package_name: version) for all pip-installed packages."""
    out_dict = PackageDict()
    for dist in metadata.distributions():
        out_dict[dist.metadata['Name']] = version.Version(dist.version)
    return out_dict

def get_installed_packages_with_available_versions(package_list = None, callback=None):
    """
    Get a list of installed packages with available versions on PyPI
    :param package_list: optional list of packages to include
    :param callback: optional callback function that accepts two integer values: current package and total packages
    :return:
    """
    installed_packages = get_installed_packages()
    if package_list is None:
        package_list = installed_packages.keys()
    else:
        # if a list of package names are given, only iterate on packages that are actually installed
        if isinstance(package_list, str):
            package_list = [package_list]
        package_list = [_pypi_canonical_name(package) for package in package_list] #convert packages to canonical names
        package_list = list(filter(lambda package: package in installed_packages, package_list))
    output_dict = PackageDict()
    total_packages = len(package_list)
    for current_package_number, package_name in enumerate(tqdm(package_list)):
        if callback is not None:
            try:
                callback(current_package_number, total_packages)
            except Exception as e:
                print("Error in callback", e)
        current_version = installed_packages[package_name]
        output_element = {}
        output_element['installed_version'] = current_version
        available_versions = get_pypi_available_versions(package_name)
        if not available_versions:
            continue # this package is not available on PyPI
        if current_version >= available_versions[0]:
            output_element['latest'] = True
        else:
            output_element['latest'] = False
        output_element['available_versions'] = available_versions
        output_dict[package_name] = output_element
    return output_dict



def standard_install_from_resource(resource_module, configuration_file_name, interactive=True):
    """
    Install packages from a resource using importlib.resources.
    :param resource_module: module containing the resource file. Can be the module itself or the module name.
    :param configuration_file_name: configuration file name
    :param interactive: (Default value = True) whether to install interactively
    :return: Nothing
    """
    if sys.version_info.minor < 10:
        import importlib_resources as pkg_resources
    else:
        import importlib.resources as pkg_resources

    from .DependencyManager import DependencyManager

    if not is_frozen():
        with pkg_resources.files(resource_module).joinpath(configuration_file_name).open() as f:
            dm = DependencyManager(config_file=f)
        if interactive:
            dm.install_interactive()
        else:
            dm.install_auto()