from packaging.markers import Marker


def process_alternatives(alternatives: list):
    """
    Process the alternatives to only show the ones relevant to the current setup
    :param alternatives: a list of strings in the format "package_name; marker"
    :return: a list of packages (without markers) that are relevant to the current setup
    """

    alternatives_out = []

    for alternative in alternatives:
        if not alternative.strip(): continue
        if ';' in alternative:
            marker = Marker(alternative.split(';')[1])
            if marker.evaluate():
                alternatives_out.append(alternative.split(';')[0].strip())
        else:
            alternatives_out.append(alternative.strip())

    return alternatives_out


def pkg_exists(pkg_name):
    """
    Check if a package exists
    :param pkg_name: the name of the package
    :return: True if the package exists, False otherwise
    """

    try:
        __import__(pkg_name)
        return True
    except ImportError:
        return False