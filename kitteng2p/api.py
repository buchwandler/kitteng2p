from __future__ import annotations

from .backends.base import PhonemeBackend
from .codec import encode_phonemes, frame_token_ids, prepare_phoneme_text
from .config import KittenG2PConfig
from .types import PhonemizeResult


class KittenG2P:
    """Convert prepared text to Kitten phonemes and framed token IDs.

    Parameters
    ----------
    config:
        Frontend and eSpeak runtime configuration. Defaults to
        :class:`KittenG2PConfig`.
    backend:
        Optional caller-owned phoneme backend. If omitted, an eSpeak backend is
        created internally and closed with this frontend.
    """

    def __init__(
        self,
        config: KittenG2PConfig | None = None,
        *,
        backend: PhonemeBackend | None = None,
    ) -> None:
        """Create a frontend and initialize its owned backend if needed.

        Parameters
        ----------
        config:
            Language, runtime mode, and optional eSpeak paths and timeout.
        backend:
            Optional caller-owned backend. Injected backends are not closed by
            this instance.
        """
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
        """Phonemize text that is already prepared and suitable to speak.

        This method does not normalize dates, currencies, units, URLs,
        abbreviations, or similar written forms. Unknown phoneme characters
        are omitted from the encoded payload and reported in
        ``PhonemizeResult.dropped_symbols``. The returned ``token_ids`` are
        framed as ``(0, *ids, 10, 0)``.

        Parameters
        ----------
        text:
            Prepared, speakable input text.

        Returns
        -------
        PhonemizeResult
            Raw and prepared phonemes, framed IDs, and dropped symbols.

        Raises
        ------
        RuntimeError
            If this frontend has already been closed.
        PhonemizationError
            If the backend cannot phonemize the input.
        """
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
        """Close an internally owned backend; injected backends remain caller-owned."""
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
    """Construct a reusable :class:`KittenG2P` frontend.

    Parameters
    ----------
    config:
        Optional frontend and eSpeak runtime configuration.
    backend:
        Optional caller-owned phoneme backend.

    Returns
    -------
    KittenG2P
        An open frontend. Close it or use it as a context manager.
    """
    return KittenG2P(config, backend=backend)


def phonemize_prepared(
    text: str,
    *,
    config: KittenG2PConfig | None = None,
    backend: PhonemeBackend | None = None,
) -> PhonemizeResult:
    """Phonemize prepared text with a temporary frontend.

    The temporary frontend is closed before returning. Injected backends remain
    caller-owned and are not closed.

    Parameters
    ----------
    text:
        Prepared, speakable input text.
    config:
        Optional frontend and eSpeak runtime configuration.
    backend:
        Optional caller-owned phoneme backend.

    Returns
    -------
    PhonemizeResult
        Phoneme details and framed Kitten token IDs.
    """
    with KittenG2P(config, backend=backend) as g2p:
        return g2p.phonemize_prepared(text)


def phonemes(
    text: str,
    *,
    config: KittenG2PConfig | None = None,
    backend: PhonemeBackend | None = None,
) -> str:
    """Return prepared phoneme text for already speakable input.

    Parameters
    ----------
    text:
        Prepared, speakable input text.
    config:
        Optional frontend and eSpeak runtime configuration.
    backend:
        Optional caller-owned phoneme backend.

    Returns
    -------
    str
        Tokenized phoneme text before character encoding.
    """
    return phonemize_prepared(text, config=config, backend=backend).phonemes


def phoneme_ids(
    text: str,
    *,
    config: KittenG2PConfig | None = None,
    backend: PhonemeBackend | None = None,
) -> tuple[int, ...]:
    """Return framed Kitten token IDs for already speakable input.

    Parameters
    ----------
    text:
        Prepared, speakable input text.
    config:
        Optional frontend and eSpeak runtime configuration.
    backend:
        Optional caller-owned phoneme backend.

    Returns
    -------
    tuple[int, ...]
        Character IDs framed with prefix ``0`` and suffix ``(10, 0)``.
    """
    return phonemize_prepared(text, config=config, backend=backend).token_ids
