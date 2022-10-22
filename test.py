"""Test file."""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from flexidep import (  # noqa: E402 pylint: disable=wrong-import-position
    DependencyManager,
)

if __name__ == '__main__':
    dm = DependencyManager()
    dm.load_file('test.cfg')

    dm.install_interactive(force_optional=False)
    # dm.install_auto(install_optional=True)
