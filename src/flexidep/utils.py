"""Utilities for the environment."""

import os
import sys

def is_conda_environment():
    """Check if the current environment is a conda environment."""
    return os.path.exists(os.path.join(sys.base_prefix, 'conda-meta'))


def is_frozen():
    """Check if the current environment is a frozen (pyinstaller) environment."""
    return getattr(sys, 'frozen', False)

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