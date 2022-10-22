"""Core module for flexidep."""
from collections import OrderedDict
from typing import NamedTuple

from packaging.markers import Marker

from .config import PackageManagers


class RequirementsTuple(NamedTuple):
    """A tuple of requirements."""

    install_before: list
    uninstall_before: list
    install_after: list
    uninstall_after: list


def get_package_managers_list():
    """
    Get a list of the available package managers.

    :return: a list of strings
    """
    pm_list = [x.name for x in PackageManagers]
    pm_list.pop(0)  # remove the first dummy package manager
    return pm_list


def parse_alternative(alternative_string: str) -> (str, list, list, list, list):
    """
    Extract the package name and the extra packages to install/uninstall.

    :param alternative_string: string,
    :return: the alternate package name
    :return: a list of packages to be installed before the main package
    :return: a list of packages to be uninstalled before the main package
    :return: a list of packages to be installed after the main package
    :return: a list of packages to be uninstalled after the main package
    """
    tokens = alternative_string.split(' ')
    package_name = tokens[0]
    install_before = []
    uninstall_before = []
    install_after = []
    uninstall_after = []

    for tok in tokens[1:]:
        if tok.startswith('++'):
            install_after.append(tok[2:])
        elif tok.startswith('--'):
            uninstall_after.append(tok[2:])
        elif tok.startswith('+'):
            install_before.append(tok[1:])
        elif tok.startswith('-'):
            uninstall_before.append(tok[1:])

    return package_name, install_before, uninstall_before, install_after, uninstall_after


def process_alternatives(alternatives: list) -> dict:
    """
    Process the alternatives to only show the ones relevant to the current setup.

    :param alternatives: a list of strings in the format "package_name; marker"
    :return: a dictionary where the keys are packages (without markers) that are relevant to the current setup,
    and the elements are the packages to install/uninstall before and after the main package
    """
    alternatives_out = OrderedDict()

    for alternative in alternatives:
        if not alternative.strip():
            continue
        if ';' in alternative:
            marker = Marker(alternative.split(';')[1])
            if marker.evaluate():
                alternative_string = alternative.split(';')[0].strip()
            else:
                alternative_string = ""
        else:
            alternative_string = alternative

        if alternative_string:
            alt, i_b, u_b, i_a, u_a = parse_alternative(alternative_string)
            alternatives_out[alt] = RequirementsTuple(
                install_before=i_b, uninstall_before=u_b, install_after=i_a, uninstall_after=u_a
            )

    return alternatives_out


def pkg_exists(pkg_name):
    """Check if a package exists.

    :param pkg_name: the name of the package
    :return: True if the package exists, False otherwise
    """
    print(f'Checking if package {pkg_name} exists...')
    try:
        __import__(pkg_name)
        print('Ok')
        return True
    except ImportError:
        return False
