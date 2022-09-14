import sys
import os

from tkinter import *

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from python_dependency_manager import DependencyManager

if __name__ == '__main__':
    dm = DependencyManager()
    dm.load_file('test.cfg')

    dm.install_interactive(force_optional=True)
