"""Installers handling functions."""

import shlex
import subprocess
import sys

from .config import PackageManagers


def install_package_with_deps(package_manager, package, dependencies, install_local, extra_command_line):
    """
    Install a package and its dependencies using the specified package manager.

    :param package_manager: the package manager to use
    :param package: the package to install
    :param dependencies: the dependencies to install. A NamedTuple as in core.py
    :param install_local: whether to install locally
    :param extra_command_line: extra command line parameters
    :return: True if success
    """
    for uninstall_before in dependencies.uninstall_before:
        if not uninstall_package(package_manager, uninstall_before):
            return False

    for install_before in dependencies.install_before:
        if not install_package(package_manager, install_before, install_local, extra_command_line):
            return False

    if not install_package(package_manager, package, install_local, extra_command_line):
        return False

    for install_after in dependencies.install_after:
        if not install_package(package_manager, install_after, install_local, extra_command_line):
            return False

    for uninstall_after in dependencies.uninstall_after:
        if not uninstall_package(package_manager, uninstall_after):
            return False

    return True


def install_package(package_manager, package, install_local, extra_command_line):
    """
    Install a package using the specified package manager.

    :param package_manager: the package manager to use
    :param package: the package to install
    :param install_local: whether to install locally
    :param extra_command_line: extra command line parameters
    :return:
    """
    if package_manager == PackageManagers.pip:
        return install_pip(package, install_local, extra_command_line)
    elif package_manager == PackageManagers.conda:
        return install_conda(package, extra_command_line)
    else:
        raise ValueError('Unknown package manager')


def install_conda(package, extra_command_line):
    """
    Install a package using conda.

    :param package: the package to install
    :param extra_command_line: extra command line parameters
    :return:
    """
    command_list = [sys.executable, '-m', 'conda', 'install', '-y']
    if extra_command_line.strip():
        command_list += shlex.split(extra_command_line)
    command_list.append(package)
    try:
        subprocess.check_call(command_list)
        return True
    except subprocess.CalledProcessError:
        return False


def install_pip(package, install_local, extra_command_line):
    """
    Install a package using pip.

    :param package: the package to install
    :param install_local: whether to install locally
    :param extra_command_line: extra command line parameters
    :return:
    """
    command_list = [sys.executable, '-m', 'pip', 'install']
    if install_local:
        command_list.append('--user')
    if extra_command_line.strip():
        command_list += shlex.split(extra_command_line)
    command_list.append(package)
    try:
        subprocess.check_call(command_list)
        return True
    except subprocess.CalledProcessError:
        return False


def uninstall_package(package_manager, package):
    """
    Uninstall a package using the specified package manager.

    :param package_manager: the package manager to use
    :param package: the package to install
    :return:
    """
    if package_manager == PackageManagers.pip:
        return uninstall_pip(package)
    elif package_manager == PackageManagers.conda:
        return uninstall_conda(package)
    else:
        raise ValueError('Unknown package manager')


def uninstall_pip(package):
    """
    Uninstall a package using pip.

    :param package: the package to uninstall
    :return:
    """
    command_list = [sys.executable, '-m', 'pip', 'uninstall', '-y', package]
    try:
        subprocess.check_call(command_list)
        return True
    except subprocess.CalledProcessError:
        return False


def uninstall_conda(package):
    """
    Uninstall a package using conda.

    :param package: the package to uninstall
    :return:
    """
    command_list = [sys.executable, '-m', 'conda', 'remove', '-y', package]
    try:
        subprocess.check_call(command_list)
        return True
    except subprocess.CalledProcessError:
        return False
