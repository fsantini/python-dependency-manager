import os
from enum import Enum
import appdirs

from .exceptions import ConfigurationError

APP_NAME = 'com.francescosantini.flexidep'
APP_AUTHOR = 'Francesco Santini'

PackageManagers = Enum('PackageManagers', 'common pip conda')

CONFIG_DIR = appdirs.user_config_dir(APP_NAME, APP_AUTHOR)
os.makedirs(CONFIG_DIR, exist_ok=True)

def ignored_packages_file(unique_id):
    if not unique_id:
        raise ConfigurationError('unique_id must be set if you want to be able to ignore packages')
    return os.path.join(CONFIG_DIR, f'{unique_id}_ignored_packages.txt')


DONT_INSTALL_TEXT = 'Do not install'
