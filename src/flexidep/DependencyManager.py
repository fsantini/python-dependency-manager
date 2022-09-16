import io
import re
from configparser import ConfigParser

from .config import PackageManagers, ignored_packages_file
from .core import process_alternatives, pkg_exists, get_package_managers_list
from .exceptions import ConfigurationError, SetupFailedError
from .installers import install_package


class DependencyManager:

    def __init__(self, config_file=None, pkg_dict=None,
                 unique_id=None,
                 interactive_initialization=True,
                 use_gui=False,
                 install_local=False,
                 package_manager=PackageManagers.pip,
                 extra_command_line=''):
        """
        Initialize the dependency manager.
        :param config_file: can be a string, a file-like object, or a path-like object
        :param pkg_dict: dictionary in the format {module_name: [list, of, alternative, sources, with, platform, markers]}
        :param unique_id: unique id for the project
        :param interactive_initialization: If True, the user will be prompted for global initialization parameters.
                            Note: this does not influence the way the user is asked for alternatives.
        :param use_gui: Controls whether a gui is displayed, or if communication is done through the console
        :param install_local: --user option for pip
        :param package_manager: pip or conda
        :return:
        """
        self.unique_id = unique_id
        self.use_gui = use_gui
        self.install_local = install_local
        self.package_manager = package_manager
        self.extra_command_line = extra_command_line
        self.initialized = not interactive_initialization
        self.pkg_to_install = {}
        self.pkg_to_install[PackageManagers.common] = {}
        for pm in get_package_managers_list():
            self.pkg_to_install[PackageManagers[pm]] = {}
        self.optional_packages = []
        self.ignored_packages = []
        if config_file:
            self.load_file(config_file)
        elif pkg_dict:
            self.load_dict(pkg_dict)

    def validate_config(self):
        """
        Validate the current configuration
        :return: Nothing
        """
        if not self.unique_id and self.optional_packages:
            raise ConfigurationError('Cannot use optional packages without a unique id')

    def load_file(self, config_file):
        """
        Load the configuration file
        :param config_file: can be a string, a file-like object, or a path-like object
        :return: Nothing
        """

        parser = ConfigParser(comment_prefixes=('#',))

        # preserve capitalization of options
        parser.optionxform = lambda option: option

        if isinstance(config_file, io.IOBase):
            parser.read_file(config_file)
        else:
            parser.read(config_file)

        # load global configuration
        if parser.has_section('Global'):
            if parser.has_option('Global', 'interactive initialization'):
                self.initialized = not parser.getboolean('Global', 'interactive initialization')

            if parser.has_option('Global', 'id'):
                self.unique_id = parser.get('Global', 'id')

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

            if parser.has_option('Global', 'optional packages'):
                opt_packages = parser.get('Global', 'optional packages').strip()
                # split the list at commas and newlines
                self.optional_packages = [x.strip() for x in re.split('[\n,]', opt_packages)]

        if parser.has_section('Packages'):
            self.pkg_to_install[PackageManagers.common] = {}
            for package, alternatives in parser.items('Packages'):
                self.pkg_to_install[PackageManagers.common][package] = \
                    process_alternatives(re.split('[\n,]', alternatives))

        package_managers = get_package_managers_list()  # list of possible package managers

        for package_manager_name in package_managers:
            # sections are always capitalized
            section_name = package_manager_name.capitalize()
            package_manager = PackageManagers[package_manager_name]
            if parser.has_section(section_name):
                self.pkg_to_install[package_manager] = {}
                for package, alternatives in parser.items(section_name):
                    self.pkg_to_install[package_manager][package] = process_alternatives(alternatives.split('\n'))

        self.validate_config()

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

        self.validate_config()

    def load_ignored_packages(self):
        """
        Get the list of ignored packages
        :return: list of ignored packages
        """
        try:
            with open(ignored_packages_file(self.unique_id), 'r') as f:
                self.ignored_packages = f.read().splitlines()
        except FileNotFoundError:
            self.ignored_packages = []

    def clear_ignored_packages(self):
        """
        Clear the ignore list
        :return: Nothing
        """
        self.ignored_packages = []
        with open(ignored_packages_file(self.unique_id), 'w') as f:
            f.write('')

    def mark_ignored(self, package):
        """
        Mark a package as ignored
        :param package: package to ignore
        :return: Nothing
        """
        print(f'Ignoring {package}')
        self.ignored_packages.append(package)
        with open(ignored_packages_file(self.unique_id), 'w') as f:
            f.write('\n'.join(self.ignored_packages))

    def install_interactive(self, force_optional=False):
        """
        Install the packages
        :param force_optional: if True, the program will ask to install optional packages even if they were already ignored once
        :return: Nothing
        """
        if not self.initialized:
            self.show_initialization()


        # compatible with python 3.6
        pkg_to_install = {**self.pkg_to_install[PackageManagers.common], **self.pkg_to_install[self.package_manager]}

        if force_optional:
            self.clear_ignored_packages()

        self.load_ignored_packages()

        for package, alternatives in pkg_to_install.items():
            if package in self.ignored_packages:
                continue
            # if the package is not installed, try to install it until it works or there are no more alternatives
            if not pkg_exists(package):
                while not self.install_package(package, alternatives, optional=package in self.optional_packages):
                    print(f'Error installing {package}. Trying a different alternative')

    def install_auto(self, install_optional=False):
        """
        Install the packages automatically
        :param install_optional: if True, optional packages will be installed
        :return: Nothing
        """

        # compatible with python 3.6
        pkg_to_install = {**self.pkg_to_install[PackageManagers.common], **self.pkg_to_install[self.package_manager]}

        for package, alternatives in pkg_to_install.items():
            if not pkg_exists(package):
                if install_optional or package not in self.optional_packages:
                    while not install_package(self.package_manager,
                                              alternatives[0],
                                              self.install_local,
                                              self.extra_command_line):
                        print(f'Error installing {package}. Trying a different alternative')
                        alternatives.pop(0)
                        if not alternatives and package not in self.optional_packages:
                            raise SetupFailedError(f'Failed to install {package}')
                        else:
                            print(f'No more alternatives for {package}. Not failing because it is optional')
                            break

    def install_package(self, package, alternatives, optional=False):
        """
        Install a package
        :param package: the package to install
        :param alternatives: a list of alternative names, recommended on top
        :param optional: if True, the package is optional and the user will be asked if he wants to install it
        :return: True if the package was installed, False otherwise
        """
        if not alternatives:
            raise SetupFailedError(f'Could not install {package}')

        if not self.initialized:
            self.show_initialization()

        source = self.select_alternative(package, alternatives, optional)
        if optional and source is None:
            self.mark_ignored(package)
            return True
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

        self.package_manager, self.install_local, self.extra_command_line = \
            interactive_initialize(self.package_manager, self.install_local, self.extra_command_line)

        self.initialized = True

    def select_alternative(self, package, alternatives, optional=False):
        """
        Select an alternative from a list of alternatives
        :param package: the provided module
        :param alternatives: list of alternatives
        :param optional: if True, the package is optional and the user will be asked if he wants to install it
        :return: the selected alternative [str]
        """
        if self.use_gui:
            from .gui import select_package_alternative
        else:
            from .cli import select_package_alternative

        return select_package_alternative(package, alternatives, optional)
