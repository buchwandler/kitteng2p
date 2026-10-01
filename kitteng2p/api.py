from __future__ import annotations

from .backends.base import PhonemeBackend
from .codec import encode_phonemes, frame_token_ids, prepare_phoneme_text
from .config import KittenG2PConfig
from .types import PhonemizeResult


class KittenG2P:
    def __init__(
        self,
        config: KittenG2PConfig | None = None,
        *,
        backend: PhonemeBackend | None = None,
    ) -> None:
        self.config = config or KittenG2PConfig()
        self._owns_backend = backend is None
        if backend is None:
            from .backends.espeak import EspeakBackend

            backend = EspeakBackend(
                mode=self.config.espeak_mode,
                executable=self.config.executable,
                library=self.config.library,
                data=self.config.data,
                timeout=self.config.timeout,
            )
        self.backend = backend
        self._closed = False

    def phonemize_prepared(self, text: str) -> PhonemizeResult:
        if self._closed:
            raise RuntimeError("KittenG2P is closed")
        raw = self.backend.phonemize(text, language=self.config.language)
        prepared = prepare_phoneme_text(raw)
        ids, dropped = encode_phonemes(prepared)
        return PhonemizeResult(
            text=text,
            raw_phonemes=raw,
            phonemes=prepared,
            token_ids=frame_token_ids(ids),
            language=self.config.language,
            dropped_symbols=dropped,
        )

    def close(self) -> None:
        if self._closed:
            return
        if self._owns_backend:
            self.backend.close()
        self._closed = True

    def __enter__(self) -> KittenG2P:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def get_g2p(
    config: KittenG2PConfig | None = None,
    *,
    backend: PhonemeBackend | None = None,
) -> KittenG2P:
    return KittenG2P(config, backend=backend)


def phonemize_prepared(
    text: str,
    *,
    config: KittenG2PConfig | None = None,
    backend: PhonemeBackend | None = None,
) -> PhonemizeResult:
    with KittenG2P(config, backend=backend) as g2p:
        return g2p.phonemize_prepared(text)


def phonemes(
    text: str,
    *,
    config: KittenG2PConfig | None = None,
    backend: PhonemeBackend | None = None,
) -> str:
    return phonemize_prepared(text, config=config, backend=backend).phonemes


def phoneme_ids(
    text: str,
    *,
    config: KittenG2PConfig | None = None,
    backend: PhonemeBackend | None = None,
) -> tuple[int, ...]:
    return phonemize_prepared(text, config=config, backend=backend).token_ids
