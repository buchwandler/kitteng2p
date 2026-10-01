from dataclasses import dataclass

import pytest

from kitteng2p import (
    KittenG2P,
    KittenG2PConfig,
    get_g2p,
    phoneme_ids,
    phonemes,
    phonemize_prepared,
)


@dataclass
class FakeBackend:
    raw_phonemes: str = "həˈloʊ, wɜːld!"
    closed: bool = False
    close_calls: int = 0

    def phonemize(self, text: str, *, language: str) -> str:
        assert language == "en-us"
        return self.raw_phonemes

    def close(self) -> None:
        self.closed = True
        self.close_calls += 1


def test_phonemize_prepared_returns_model_ids_and_preserves_injected_ownership():
    backend = FakeBackend()
    g2p = KittenG2P(KittenG2PConfig(), backend=backend)

    result = g2p.phonemize_prepared("Hello, world.")

    assert result.text == "Hello, world."
    assert result.raw_phonemes == backend.raw_phonemes
    assert result.phonemes == "həˈloʊ , wɜːld !"
    assert result.token_ids[0] == 0
    assert result.token_ids[-2:] == (10, 0)
    assert result.dropped_symbols == ()
    assert result.ids == result.token_ids
    g2p.close()
    assert not backend.closed


def test_empty_text_uses_only_model_framing():
    result = KittenG2P(backend=FakeBackend(raw_phonemes="")).phonemize_prepared("")
    assert result.token_ids == (0, 10, 0)


def test_close_is_idempotent_and_use_after_close_raises():
    backend = FakeBackend()
    g2p = KittenG2P(backend=backend)

    g2p.close()
    g2p.close()

    assert backend.close_calls == 0
    with pytest.raises(RuntimeError, match="closed"):
        g2p.phonemize_prepared("Hello")


def test_internally_owned_backend_is_closed_once(monkeypatch):
    import kitteng2p.backends.espeak as espeak_backend

    backend = FakeBackend()
    monkeypatch.setattr(espeak_backend, "EspeakBackend", lambda **_: backend)

    g2p = KittenG2P()
    g2p.close()
    g2p.close()

    assert backend.closed
    assert backend.close_calls == 1


def test_get_g2p_returns_frontend():
    g2p = get_g2p(backend=FakeBackend())
    assert isinstance(g2p, KittenG2P)
    g2p.close()


def test_convenience_functions_return_prepared_results():
    result = phonemize_prepared("Hello", backend=FakeBackend())
    assert result.text == "Hello"
    assert result.phonemes == "həˈloʊ , wɜːld !"

    assert phonemes("Hello", backend=FakeBackend()) == "həˈloʊ , wɜːld !"
    ids = phoneme_ids("Hello", backend=FakeBackend())
    assert ids[0] == 0
    assert ids[-2:] == (10, 0)
