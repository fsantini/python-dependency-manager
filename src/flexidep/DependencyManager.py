"""Definition of DependencyManager class."""

import io
import re
from collections import OrderedDict
from configparser import ConfigParser

from .config import PackageManagers, ignored_packages_file
from .core import get_package_managers_list, pkg_exists, process_alternatives
from .exceptions import ConfigurationError, SetupFailedError
from .installers import install_package_with_deps, uninstall_package


class DependencyManager:
    """Class managing a project's dependency information."""

    def __init__(
        self,
        config_file=None,
        config_string=None,
        unique_id=None,
        interactive_initialization=True,
        use_gui=False,
        install_local=False,
        package_manager=PackageManagers.pip,
        extra_command_line='',
    ):
        """
        Initialize the dependency manager.

        :param config_file: can be a string, a file-like object, or a path-like object
        :param pkg_dict: dictionary in the format
            {module_name: [list, of, alternative, sources, with, platform, markers]}
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
        for pkg_mgr in get_package_managers_list():
            self.pkg_to_install[PackageManagers[pkg_mgr]] = {}
        self.optional_packages = []
        self.ignored_packages = []
        self.priority_list = []
        self.pkg_to_uninstall = {}
        self.pkg_to_uninstall[PackageManagers.common] = []
        if config_file:
            self.load_file(config_file)
        elif config_string:
            self.load_string(config_string)

    def validate_config(self):
        """
        Validate the current configuration.

        :return: Nothing
        """
        if not self.unique_id and self.optional_packages:
            raise ConfigurationError('Cannot use optional packages without a unique id')

    def load_file(self, config_file):
        """
        Load the configuration from a file.

        :param config_file: can be a string, a file-like object, or a path-like object
        :return: Nothing
        """
        self.load_config(config_file, False)

    def load_string(self, config_string):
        """
        Load the configuration from a string.

        :param config_string: string containing the configuration
        :return: Nothing
        """
        self.load_config(config_string, True)

    def load_config(self, config, is_configuration_string=False):
        """
        Load the configuration.

        :param config: can be a string, a file-like object, or a path-like object
        :param is_configuration_string: True if the config is a string containing the configuration itself
        :return: Nothing
        """
        parser = ConfigParser(comment_prefixes=('#',))

        # preserve capitalization of options
        parser.optionxform = lambda option: option

        if is_configuration_string:
            parser.read_string(config)
        else:
            if isinstance(config, io.IOBase):
                parser.read_file(config)
            else:
                parser.read(config)

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

            if parser.has_option('Global', 'priority'):
                priority_str = parser.get('Global', 'priority').strip()
                # split the list at commas and newlines
                self.priority_list = [x.strip() for x in re.split('[\n,]', priority_str)]

            package_manager_suffixes = [''] + [
                f'.{package_manager.lower()}' for package_manager in get_package_managers_list()
            ]

            for package_manager_suffix in package_manager_suffixes:
                if parser.has_option('Global', 'uninstall' + package_manager_suffix):
                    uninstall_str = parser.get('Global', 'uninstall' + package_manager_suffix).strip()
                    if package_manager_suffix == '':
                        dict_key = PackageManagers.common
                    else:
                        dict_key = PackageManagers[package_manager_suffix[1:]]
                    # split the list at commas and newlines
                    self.pkg_to_uninstall[dict_key] = [x.strip() for x in re.split('[\n,]', uninstall_str)]

        if parser.has_section('Packages'):
            self.pkg_to_install[PackageManagers.common] = {}
            for package, alternatives in parser.items('Packages'):
                self.pkg_to_install[PackageManagers.common][package] = process_alternatives(
                    re.split('[\n,]', alternatives)
                )

        package_managers = get_package_managers_list()  # list of possible package managers

        for package_manager_name in package_managers:
            # sections are always capitalized
            section_name = package_manager_name.capitalize()
            package_manager = PackageManagers[package_manager_name]
            if parser.has_section(section_name):
                self.pkg_to_install[package_manager] = {}
                for package, alternatives in parser.items(section_name):
                    self.pkg_to_install[package_manager][package] = process_alternatives(
                        re.split('[\n,]', alternatives)
                    )

        self.validate_config()

    def load_ignored_packages(self):
        """
        Get the list of ignored packages.

        :return: list of ignored packages
        """
        try:
            with open(ignored_packages_file(self.unique_id), encoding='utf8') as fd:
                self.ignored_packages = fd.read().splitlines()
        except FileNotFoundError:
            self.ignored_packages = []

        # remove packages that are not optional anymore
        for package in self.ignored_packages[:]:
            if package not in self.optional_packages:
                self.ignored_packages.remove(package)

        self.save_ignored_packages()

    def clear_ignored_packages(self):
        """
        Clear the ignore list.

        :return: Nothing
        """
        self.ignored_packages = []
        with open(ignored_packages_file(self.unique_id), 'w', encoding='utf-8') as fd:
            fd.write('')

    def mark_ignored(self, package):
        """
        Mark a package as ignored.

        :param package: package to ignore
        :return: Nothing
        """
        self.ignored_packages.append(package)
        self.save_ignored_packages()

    def save_ignored_packages(self):
        """
        Save the list of ignored packages.

        :return: Nothing
        """
        with open(ignored_packages_file(self.unique_id), 'w', encoding='utf-8') as fd:
            fd.write('\n'.join(self.ignored_packages))

    def sort_packages(self, pkg_dict):
        """
        Sort the packages according to the priority list.

        :param pkg_dict: dictionary of packages to sort
        :return: sorted list of packages
        """
        if not self.priority_list:
            return

        # the first package in the priority list will end up as the first package in the ordered dict
        for package in self.priority_list[::-1]:
            if package in pkg_dict:
                pkg_dict.move_to_end(package, last=False)  # move package to the beginning

    def install_interactive(self, force_optional=False):
        """
        Install the packages.

        :param force_optional: if True, the program will ask to install optional packages even if they were already
            ignored once
        :return: Nothing
        """
        if not self.initialized:
            self.show_initialization()

        # uninstall packages
        pkg_to_uninstall_list = (
            self.pkg_to_uninstall[PackageManagers.common] + self.pkg_to_uninstall[self.package_manager]
        )
        for pkg in pkg_to_uninstall_list:
            self.uninstall_package(pkg, interactive=True)

        # compatible with python 3.6
        pkg_to_install = OrderedDict(
            {**self.pkg_to_install[PackageManagers.common], **self.pkg_to_install[self.package_manager]}
        )

        self.sort_packages(pkg_to_install)

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
        Install the packages automatically.

        :param install_optional: if True, optional packages will be installed
        :return: Nothing
        """
        # uninstall packages
        pkg_to_uninstall_list = (
            self.pkg_to_uninstall[PackageManagers.common] + self.pkg_to_uninstall[self.package_manager]
        )
        for pkg in pkg_to_uninstall_list:
            self.uninstall_package(pkg, interactive=False)

        # compatible with python 3.6
        pkg_to_install = OrderedDict(
            {**self.pkg_to_install[PackageManagers.common], **self.pkg_to_install[self.package_manager]}
        )

        self.sort_packages(pkg_to_install)

        for package, alternatives in pkg_to_install.items():
            if not pkg_exists(package):
                if install_optional or package not in self.optional_packages:
                    while not install_package_with_deps(
                        self.package_manager,
                        next(iter(alternatives.keys())),
                        next(iter(alternatives.values())),
                        self.install_local,
                        self.extra_command_line,
                    ):
                        print(f'Error installing {package}. Trying a different alternative')
                        alternatives.popitem(0)
                        if not alternatives:
                            if package in self.optional_packages:
                                print(f'No more alternatives for {package}. Not failing because it is optional')
                                break
                            raise SetupFailedError(f'Failed to install {package}')

    def uninstall_package(self, package, interactive=True):
        """
        Uninstall a package.

        :param package: package to uninstall
        :param interactive: if True, the user will be asked to confirm the uninstallation
        :return: Nothing
        """
        if interactive:
            if self.use_gui:
                from .gui import notify_uninstall
            else:
                from .cli import notify_uninstall

            if not notify_uninstall(package):
                raise SetupFailedError(f'Uninstallation of {package} aborted by user')

        uninstall_package(self.package_manager, package)

    def install_package(self, package, alternatives, optional=False):
        """
        Install a package.

        :param package: the package to install
        :param alternatives: a list of alternative names, recommended on top
        :param optional: if True, the package is optional and the user will be asked if he wants to install it
        :return: True if the package was installed, False otherwise
        """
        if not alternatives:
            raise SetupFailedError(f'Could not install {package}')

        if not self.initialized:
            self.show_initialization()

        alternative_names = list(alternatives.keys())
        source = self.select_alternative(package, alternative_names, optional)
        if optional and source is None:
            self.mark_ignored(package)
            return True
        dependencies = alternatives[source]
        del alternatives[source]

        return install_package_with_deps(
            self.package_manager, source, dependencies, self.install_local, self.extra_command_line
        )

    def show_initialization(self):
        """
        Show the initialization interface.

        :return: Nothing
        """
        # pylint: disable=import-outside-toplevel
        if self.use_gui:
            from .gui import interactive_initialize
        else:
            from .cli import interactive_initialize

        self.package_manager, self.install_local, self.extra_command_line = interactive_initialize(
            self.package_manager, self.install_local, self.extra_command_line
        )

        self.initialized = True

    def select_alternative(self, package, alternatives, optional=False):
        """
        Select an alternative from a list of alternatives.

        :param package: the provided module
        :param alternatives: list of alternatives
        :param optional: if True, the package is optional and the user will be asked if he wants to install it
        :return: the selected alternative [str]
        """
        # pylint: disable=import-outside-toplevel
        if self.use_gui:
            from .gui import select_package_alternative
        else:
            from .cli import select_package_alternative

        return select_package_alternative(package, alternatives, optional)
