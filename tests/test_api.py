from dataclasses import dataclass

from kitteng2p import KittenG2P, KittenG2PConfig


@dataclass
class FakeBackend:
    closed: bool = False

    def phonemize(self, text: str, *, language: str) -> str:
        assert language == "en-us"
        return "həˈloʊ, wɜːld!"

    def close(self) -> None:
        self.closed = True


def test_phonemize_prepared_returns_model_ids():
    backend = FakeBackend()
    g2p = KittenG2P(KittenG2PConfig(), backend=backend)
    result = g2p.phonemize_prepared("Hello, world.")
    assert result.phonemes == "həˈloʊ , wɜːld !"
    assert result.token_ids[0] == 0
    assert result.token_ids[-2:] == (10, 0)
    assert result.dropped_symbols == ()
    g2p.close()
    assert backend.closed is False  # injected dependencies are caller-owned


def test_empty_text_is_still_framed():
    result = KittenG2P(backend=FakeBackend()).phonemize_prepared("")
    assert result.token_ids[0] == 0
    assert result.token_ids[-2:] == (10, 0)
