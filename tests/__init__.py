import pkg_resources
from packaging.version import Version

import ics


def test_version_matches():
    assert Version(ics.__version__) == Version(pkg_resources.get_distribution('ics').version)
