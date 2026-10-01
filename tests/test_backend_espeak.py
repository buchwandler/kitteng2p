import os
import sys
from types import ModuleType, SimpleNamespace

import pytest

from kitteng2p import BackendUnavailableError, KittenG2P, PhonemizationError
from kitteng2p.backends.espeak import EspeakBackend, _compose_clauses


def test_compose_clauses_covers_punctuation_empty_payload_and_missing_terminator():
    clauses = [
        SimpleNamespace(phonemes="alpha", terminator=","),
        SimpleNamespace(phonemes="beta", terminator=":"),
        SimpleNamespace(phonemes="gamma", terminator=";"),
        SimpleNamespace(phonemes="delta", terminator="."),
        SimpleNamespace(phonemes="epsilon", terminator="?"),
        SimpleNamespace(phonemes="zeta", terminator="!"),
        SimpleNamespace(phonemes="", terminator="!"),
        SimpleNamespace(phonemes="eta", terminator=None),
        SimpleNamespace(phonemes="theta", terminator=""),
    ]

    assert _compose_clauses(clauses) == (
        "alpha , beta : gamma ; delta . epsilon ? zeta ! ! eta theta"
    )


def test_backend_falls_back_when_clause_rendering_is_empty():
    class Runtime:
        def clauses(self, text: str, *, voice: str):
            return []

        def phonemize(self, text: str, *, voice: str) -> str:
            return "fallback"

    backend = EspeakBackend.__new__(EspeakBackend)
    backend._runtime = Runtime()

    assert backend.phonemize("hello", language="en-us") == "fallback"


def test_runtime_initialization_errors_preserve_cause(monkeypatch):
    class BrokenRuntime:
        def __init__(self, **kwargs):
            raise ValueError("runtime setup failed")

    module = ModuleType("espeakng_runtime")
    module.EspeakRuntime = BrokenRuntime
    monkeypatch.setitem(sys.modules, "espeakng_runtime", module)

    with pytest.raises(BackendUnavailableError) as error:
        EspeakBackend()

    assert isinstance(error.value.__cause__, ValueError)


def test_phonemization_errors_preserve_cause():
    class BrokenRuntime:
        def clauses(self, text: str, *, voice: str):
            raise ValueError("phonemization failed")

    backend = EspeakBackend.__new__(EspeakBackend)
    backend._runtime = BrokenRuntime()

    with pytest.raises(PhonemizationError) as error:
        backend.phonemize("hello", language="en-us")

    assert isinstance(error.value.__cause__, ValueError)


@pytest.mark.espeak
@pytest.mark.integration
def test_live_hello_world():
    if os.environ.get("KITTENG2P_RUN_ESPEAK_TESTS") != "1":
        pytest.skip("Set KITTENG2P_RUN_ESPEAK_TESTS=1 to run the live eSpeak check")

    with KittenG2P() as g2p:
        result = g2p.phonemize_prepared("Hello world.")

    assert result.raw_phonemes
    assert result.token_ids[0] == 0
    assert result.token_ids[-2:] == (10, 0)
