import io
import sys
from configparser import ConfigParser
import shlex
import subprocess

from .config import PackageManagers
from .core import process_alternatives, pkg_exists, SetupFailedError, get_package_managers_list
from .installers import install_package


class DependencyManager:

    def __init__(self, config_file=None, pkg_dict=None, interactive_initialization=True,
                 use_gui=False,
                 install_local=False,
                 package_manager=PackageManagers.pip,
                 extra_command_line=''):
        """
        Initialize the dependency manager.

        :param interactive_initialization: If True, the user will be prompted for global initialization parameters.
        :param use_gui: Controls whether a gui is displayed, or if communication is done through the console
        :param install_local: --user option for pip
        :param package_manager: pip or conda
        :return:
        """
        self.use_gui = use_gui
        self.install_local = install_local
        self.package_manager = package_manager
        self.extra_command_line = extra_command_line
        self.initialized = not interactive_initialization
        self.pkg_to_install = {}

    def load_file(self, config_file):
        """
        Load the configuration file
        :param config_file: can be a string, a file-like object, or a path-like object
        :return: Nothing
        """

        parser = ConfigParser(comment_prefixes=('#',))

        if isinstance(config_file, io.IOBase):
            parser.read_file(config_file)
        else:
            parser.read(config_file)

        # load global configuration
        if parser.has_section('Global'):
            if parser.has_option('Global', 'use gui'):
                self.use_gui = parser.getboolean('Global', 'use gui')

            if parser.has_option('Global', 'local install'):
                self.install_local = parser.getboolean('Global', 'local install')

            if parser.has_option('Global', 'package manager'):
                configured_manager = parser.get('Global', 'package manager')
                try:
                    self.package_manager = PackageManagers[configured_manager]
                except KeyError:
                    print('Warning: invalid package manager in configuration file. Using pip')
                    self.package_manager = PackageManagers.pip

            if parser.has_option('Global', 'extra command line'):
                self.extra_command_line = parser.get('Global', 'extra command line')

        if parser.has_section('Packages'):
            self.pkg_to_install[PackageManagers.common] = {}
            for package, alternatives in parser.items('Packages'):
                self.pkg_to_install[PackageManagers.common][package] = process_alternatives(alternatives.split('\n'))

        package_managers = get_package_managers_list()  # list of possible package managers

        for package_manager_name in package_managers:
            # sections are always capitalized
            section_name = package_manager_name.capitalize()
            package_manager = PackageManagers[package_manager_name]
            if parser.has_section(section_name):
                self.pkg_to_install[package_manager] = {}
                for package, alternatives in parser.items(section_name):
                    self.pkg_to_install[package_manager][package] = process_alternatives(alternatives.split('\n'))

    def load_dict(self, pkg_dict):
        """
        Load the configuration from a dictionary
        :param pkg_dict: dictionary in the format {module_name: [list, of, alternatives, with, platform, markers]}
        :return: Nothing
        """

        self.pkg_to_install[PackageManagers.common] = {}

        for package, alternatives in pkg_dict.items():
            alternatives = process_alternatives(alternatives)
            self.pkg_to_install[PackageManagers.common][package] = alternatives

    def install_all(self):
        """
        Install the packages
        :return: Nothing
        """
        if not self.initialized:
            self.show_initialization()

        # compatible with python 3.6
        pkg_to_install = {**self.pkg_to_install[PackageManagers.common], **self.pkg_to_install[self.package_manager]}

        for package, alternatives in pkg_to_install.items():
            # if the package is not installed, try to install it until it works or there are no more alternatives
            if not pkg_exists(package):
                while not self.install_package(package, alternatives):
                    print(f'Error installing {package}. Trying a different alternative')

    def install_package(self, package, alternatives):
        """
        Install a package
        :param package: the package to install
        :param alternatives: a list of alternative names, recommended on top
        :return: True if the package was installed, False otherwise
        """
        if not alternatives:
            raise SetupFailedError(f'Could not install {package}')

        if not self.initialized:
            self.show_initialization()

        source = self.select_alternative(package, alternatives)
        alternatives.remove(source)

        return install_package(self.package_manager, source, self.install_local, self.extra_command_line)

    def show_initialization(self):
        """
        Show the initialization interface
        :return: Nothing
        """

        if self.use_gui:
            from .gui import interactive_initialize
        else:
            from .cli import interactive_initialize

        self.package_manager, self.install_local, self.extra_command_line = interactive_initialize(self.package_manager, self.install_local, self.extra_command_line)
        print(self.package_manager, self.install_local, self.extra_command_line)

        self.initialized = True

    def select_alternative(self, package, alternatives):
        """
        Select an alternative from a list of alternatives
        :param package: the provided module
        :param alternatives: list of alternatives
        :return: the selected alternative [str]
        """
        if self.use_gui:
            from .gui import select_package_alternative
        else:
            from .cli import select_package_alternative

        return select_package_alternative(package, alternatives)


