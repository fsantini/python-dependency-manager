![PyPI - Python Version](https://img.shields.io/pypi/pyversions/flexidep)
[![PyPI version](https://badge.fury.io/py/flexidep.svg)](https://badge.fury.io/py/flexidep)
![GitHub](https://img.shields.io/github/license/fsantini/python-dependency-manager)

# Flexidep
Package to manage optional and alternate dependencies in python packages.

This package checks for dependencies at runtime and provides an interface to install them.  It supports multiple
alternatives, so that the user can choose which package to install.

Choice for pip and conda are provided.

## Usage

This package is intended to be configured using a cfg file (similar to setup.cfg) and to be called at runtime during the
initialization of the containing module or program, before any import is done. It reads all the modules that are
required and tries to install them.

The installation can either be interactive or automatic, depending on the intended usage.

For the interactive installation, a command-line interface or a GUI based on tk are provided.

### Integration in your code

```python
from flexidep import DependencyManager, SetupFailedError, OperationCanceledError

dm = DependencyManager()
dm.load_file('test.cfg')
try:
    dm.install_interactive(force_optional=True)
except OperationCanceledError:
    print('Installation canceled')
except SetupFailedError:
    print('Setup failed')
```

If you have a configuration file inside a python module, you can use the following simplified code:
```python
from flexidep import standard_install_from_resource
from . import resources # assuming that "resources" is the name of the module where you have the configuration file
standard_install_from_resource(resources, 'runtime_dependencies.cfg')
````

For manual control, a `DependencyManager` object is created with the following parameters:
```python
DependencyManager(
    config_file=None,
    config_string=None,
    unique_id=None,
    interactive_initialization=True,
    use_gui=False,
    install_local=False,
    package_manager=PackageManagers.pip,
    extra_command_line='',
)
```

* `config_file`: path to the configuration file. It can be a string, a Path-like object or a file-like object.
**Note**: all configuration options in a config file supersede the options specified in the constructor.
* `config_string`: string containing the configuration in config file format. If both `config_file` and `config_string` are provided, the file is used.
* `unique_id`: unique identifier for the project. It is used to store the configuration in the user's home directory.
* `interactive_initialization`: if True, the user is asked to choose the global installation parameters.
* `use_gui`: if True, a GUI is used for the interactive installation.
* `install_local`: if True, the packages are installed locally in the current environment (`--user` flag to pip)
* `package_manager`: package manager to use. Can be `PackageManagers.pip` or `PackageManagers.conda`.
* `extra_command_line`: extra command line arguments to pass to the package manager.


The main functions that are used are:
* `load_file(file)` to load the configuration file. `file` can be a file name, a file object, or a path-like object.
* `install_interactive(force_optional)` to install the dependencies in interactive mode. If force_optional is false,
  optional dependencies will only be asked once and the choice will be remembered. If it is true, the choices are
  cleared and the optional dependencies are asked again.
* `install_auto(install_optional)` to install the dependencies in automatic mode. If install_optional is true, optional
  dependencies are installed too, otherwise only the required ones are.

#### Utility functions
The following functions are provided for convenience:
* `is_conda()` returns True if the current environment is a conda environment.
* `is_frozen()` returns True if the current environment is frozen (e.g. using pyinstaller).

### Configuration file
A typical configuration file is the following:
```ini
[Global]
# Whether to let the user specify the global options (e.g. pip or conda)
interactive initialization = True
# Whether to use the tk gui or not
use gui = True
# Whether to pass the --user flag to pip
local install = False
# Which package manager to use (pip and conda are currently supported)
package manager = pip
# A unique identifier for the app that calls the package
# (used to store the optional package choices)
id = com.myname.myproject
# a list (comma or newline-separated) of packages that are optional.
# The default status of a package is required
optional packages =
    tensorflow

# Defines a priority order for the packages to be installed
priority = my_pip_package, tensorflow

# Here you can specify which packages should be uninstalled because they conflict with this package
uninstall = conflict_package
# package-manager-specific packages can be defined like this
uninstall.pip = conflict_package_pip
uninstall.conda = conflict_package_conda

# This section contains list of packages to be installed.
# The name of each entry is the name of the *module* that the package provides.
# For example, tensorflow-gpu and tensorflow-cpu both provide the tensorflow module.
# The name of the entry is therefore "tensorflow".
# After the name, the list of packages is given, separated by newlines.
# Environment markers can also be provided, so that the user is only presented with options
# that are compatible with the current environment.
[Packages]
tensorflow =
    tensorflow_gpu ; sys_platform != 'darwin'
    tensorflow_cpu ; sys_platform != 'darwin'
    tensorflow_metal ; sys_platform == 'darwin'
    tensorflow_macos ; sys_platform == 'darwin'

# Alternatives to be checked can also be specified, separated by a pipe character.
# For example, this checks that either PyQt5 or PySide2 is installed and prompts to
# install one of them if none is found.
PyQt5|PySide2 =
    PyQt5
    PySide2

# dependencies and conflicts can be specified for each alternative
# this is useful if this package automatically installs something that
# is unwanted with the rest of the package.
package_with_dependencies =
    package_1 +install_before_package1 +install_before_package2 -uninstall_before_package --uninstall_after_package ++install_after_package

[Pip]
# pip-specific packages. These packages will only be installed if pip is used as a manager.
my_pip_package =
    pip_package_1
    pip_package_2

[Conda]
# conda-specific packages
``
