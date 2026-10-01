import pytest

from kitteng2p import KittenG2PConfig


def test_defaults():
    assert KittenG2PConfig() == KittenG2PConfig(
        language="en-us",
        espeak_mode="auto",
        executable=None,
        library=None,
        data=None,
        timeout=None,
    )


def test_invalid_espeak_mode():
    with pytest.raises(ValueError, match="espeak_mode"):
        KittenG2PConfig(espeak_mode="invalid")


@pytest.mark.parametrize("language", ["", " ", "\t"])
def test_empty_language_is_rejected(language: str):
    with pytest.raises(ValueError, match="language"):
        KittenG2PConfig(language=language)


@pytest.mark.parametrize("timeout", [0, -1])
def test_nonpositive_timeout_is_rejected(timeout: float):
    with pytest.raises(ValueError, match="timeout"):
        KittenG2PConfig(timeout=timeout)


def test_positive_timeout_and_explicit_paths_are_preserved():
    config = KittenG2PConfig(
        executable="/opt/espeak-ng",
        library="/opt/libespeak-ng.so",
        data="/opt/espeak-ng-data",
        timeout=2.5,
    )

    assert config.executable == "/opt/espeak-ng"
    assert config.library == "/opt/libespeak-ng.so"
    assert config.data == "/opt/espeak-ng-data"
    assert config.timeout == 2.5
