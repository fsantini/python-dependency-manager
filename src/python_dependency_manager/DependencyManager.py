import io
from configparser import ConfigParser
from enum import Enum

from .core import process_alternatives, pkg_exists, SetupFailedError

PackageManagers = Enum('PackageManagers', 'common pip conda')


class DependencyManager:

    def __init__(self, config_file=None, pkg_dict=None, interactive_initialization=True, use_gui=False, install_local=False, package_manager=PackageManagers.pip):
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
        self.initialized = not interactive_initialization
        self.pkg_to_install = {}


    def load_file(self, config_file):
        """
        Load the configuration file
        :param config_file: can be a string, a file-like object, or a path-like object
        :return:
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
                if parser.get('Global', 'package manager') == 'conda':
                    self.package_manager = PackageManagers.conda
                else:
                    self.package_manager = PackageManagers.pip

        if parser.has_section('Packages'):
            self.pkg_to_install[PackageManagers.common] = {}
            for package, alternatives in parser.items('Packages'):
                self.pkg_to_install[PackageManagers.common][package] = process_alternatives(alternatives.split('\n'))

        if parser.has_section('Pip'):
            self.pkg_to_install[PackageManagers.pip] = {}
            for package, alternatives in parser.items('Pip'):
                self.pkg_to_install[PackageManagers.pip][package] = process_alternatives(alternatives.split('\n'))

        if parser.has_section('Conda'):
            self.pkg_to_install[PackageManagers.conda] = {}
            for package, alternatives in parser.items('Conda'):
                self.pkg_to_install[PackageManagers.conda][package] = process_alternatives(alternatives.split('\n'))


    def load_dict(self, pkg_dict):
        """
        Load the configuration from a dictionary
        :param config_dict:
        :return:
        """

        self.pkg_to_install[PackageManagers.common] = {}

        for package, alternatives in pkg_dict.items():
            alternatives = process_alternatives(alternatives)
            self.pkg_to_install[PackageManagers.common][package] = alternatives


    def install_all(self):
        """
        Install the packages
        :return:
        """
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
        :return:
        """
        if not alternatives:
            raise SetupFailedError(f'Could not install {package}')

        if not self.initialized:
            self.show_initialization()

        source = self.select_alternative(package, alternatives)

        if self.package_manager == PackageManagers.conda:
            return self.install_conda(source)
        else:
            return self.install_pip(source)



