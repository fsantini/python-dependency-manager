"""Exception classes definitions."""


class SetupFailedError(Exception):
    """Exception raised if the setup function failed."""


class OperationCanceledError(Exception):
    """Exception raised an operation is cancelled by the user."""


class ConfigurationError(Exception):
    """Exception raised if the configuration contains errors."""
