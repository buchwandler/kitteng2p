from importlib.metadata import PackageNotFoundError, version

import kitteng2p


def test_public_version_matches_distribution_metadata():
    try:
        expected = version("kitteng2p")
    except PackageNotFoundError:
        expected = "0+unknown"
    assert kitteng2p.__version__ == expected
