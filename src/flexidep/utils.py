# utilities for environment
import os
import sys


def is_conda_environment():
    """Check if the current environment is a conda environment"""
    return os.path.exists(os.path.join(sys.base_prefix, 'conda-meta'))


def is_frozen():
    """Check if the current environment is a frozen (pyinstaller) environment"""
    return getattr(sys, 'frozen', False)
