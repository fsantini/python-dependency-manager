import subprocess
import sys
import shlex

from .config import PackageManagers


def install_package(package_manager, package, install_local, extra_command_line):
    """
    Install a package using the specified package manager
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
    Install a package using conda
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
    Install a package using pip
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
