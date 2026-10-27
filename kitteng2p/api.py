from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from .backends.base import PhonemeBackend
from .codec import SYMBOL_TO_ID, encode_phonemes, frame_token_ids, prepare_phoneme_text
from .config import KittenG2PConfig
from .context import ContextResolution, resolve_english_heteronym
from .lexicons import LoadedLexiconSource, open_g2lex_sources
from .types import (
    LinguisticToken,
    PhonemizeResult,
    PronunciationOverride,
    PronunciationTrace,
)

_WORD_RE = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)
_PUNCTUATION = frozenset(",.;:!?…—-–'\"“”‘’()[]{}«»")


def _as_token(value: LinguisticToken | Mapping[str, Any]) -> LinguisticToken:
    if isinstance(value, LinguisticToken):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("tokens must contain LinguisticToken values or mappings")
    try:
        return LinguisticToken(
            start=value["start"],
            end=value["end"],
            text=value["text"],
            pos=value.get("pos"),
            tag=value.get("tag"),
            lemma=value.get("lemma"),
            morph=value.get("morph"),
            language=value.get("language"),
        )
    except KeyError as exc:
        raise ValueError(f"linguistic token is missing required field {exc.args[0]!r}") from exc


def _as_override(value: PronunciationOverride | Mapping[str, Any]) -> PronunciationOverride:
    if isinstance(value, PronunciationOverride):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("pronunciation overrides must be typed values or mappings")
    try:
        return PronunciationOverride(
            start=value["start"],
            end=value["end"],
            phonemes=value["phonemes"],
            language=value.get("language"),
            alphabet=value.get("alphabet", "ipa"),
        )
    except KeyError as exc:
        raise ValueError(
            f"pronunciation override is missing required field {exc.args[0]!r}"
        ) from exc


def _word_tokens(text: str) -> tuple[LinguisticToken, ...]:
    return tuple(
        LinguisticToken(match.start(), match.end(), match.group())
        for match in _WORD_RE.finditer(text)
    )


def _normalize_tokens(
    text: str,
    values: (
        Sequence[LinguisticToken | Mapping[str, Any]] | LinguisticToken | Mapping[str, Any] | None
    ),
) -> tuple[LinguisticToken, ...]:
    words = _word_tokens(text)
    if values is None:
        return words
    supplied = (values,) if isinstance(values, (LinguisticToken, Mapping)) else tuple(values)
    tokens = sorted((_as_token(value) for value in supplied), key=lambda item: item.start)
    by_span = {(word.start, word.end): word for word in words}
    previous_end = -1
    aligned: dict[tuple[int, int], LinguisticToken] = {}
    for token in tokens:
        if token.end > len(text):
            raise ValueError(
                f"linguistic token span [{token.start}, {token.end}) exceeds "
                f"text length {len(text)}"
            )
        if text[token.start : token.end] != token.text:
            raise ValueError(
                f"linguistic token text {token.text!r} does not match source text at "
                f"span [{token.start}, {token.end})"
            )
        span = (token.start, token.end)
        if token.start < previous_end:
            raise ValueError("linguistic token spans must not overlap")
        if span not in by_span:
            raise ValueError(
                f"linguistic token span [{token.start}, {token.end}) must align to one source word"
            )
        aligned[span] = token
        previous_end = token.end
    return tuple(aligned.get((word.start, word.end), word) for word in words)


def _normalize_overrides(
    text: str,
    values: Sequence[PronunciationOverride | Mapping[str, Any]]
    | PronunciationOverride
    | Mapping[str, Any]
    | None,
    language: str,
    tokens: tuple[LinguisticToken, ...],
) -> tuple[PronunciationOverride, ...]:
    if values is None:
        return ()
    supplied = (values,) if isinstance(values, (PronunciationOverride, Mapping)) else tuple(values)
    overrides = sorted((_as_override(value) for value in supplied), key=lambda item: item.start)
    word_spans = {(token.start, token.end) for token in tokens}
    previous_end = -1
    for override in overrides:
        if override.end > len(text):
            raise ValueError(
                f"pronunciation override span [{override.start}, {override.end}) exceeds "
                f"text length {len(text)}"
            )
        if override.start < previous_end:
            raise ValueError("explicit pronunciation override spans must not overlap")
        if override.language and (
            override.language.casefold().replace("_", "-") != language.casefold().replace("_", "-")
        ):
            raise ValueError(
                f"pronunciation override language {override.language!r} does not match "
                f"request language {language!r}"
            )
        covered = [
            span for span in word_spans if override.start <= span[0] and span[1] <= override.end
        ]
        if (
            not covered
            or min(start for start, _ in covered) != override.start
            or max(end for _, end in covered) != override.end
        ):
            raise ValueError(
                f"pronunciation override span [{override.start}, {override.end}) must cover "
                "one or more complete source words"
            )
        _validate_ipa(override.phonemes, text[override.start : override.end], "explicit override")
        previous_end = override.end
    return tuple(overrides)


def _validate_ipa(phonemes: str, source_text: str, source_name: str) -> str:
    value = phonemes.strip()
    for symbol in value:
        if not symbol.isspace() and symbol not in SYMBOL_TO_ID:
            raise ValueError(
                f"Pronunciation for {source_text!r} from {source_name!r} contains unsupported "
                f"Kitten phoneme symbol {symbol!r}. The pronunciation was not silently truncated."
            )
    prepared = prepare_phoneme_text(value)
    _ids, dropped = encode_phonemes(prepared)
    if dropped:
        symbol = dropped[0]
        raise ValueError(
            f"Pronunciation for {source_text!r} from {source_name!r} contains unsupported "
            f"Kitten phoneme symbol {symbol!r}. The pronunciation was not silently truncated."
        )
    if not prepared:
        raise ValueError(f"Pronunciation for {source_text!r} from {source_name!r} is empty")
    return value


def _tag_pos(tag: str | None) -> str | None:
    if not tag:
        return None
    value = tag.upper()
    if value.startswith("NN"):
        return "NOUN"
    if value.startswith("VB"):
        return "VERB"
    if value.startswith("JJ"):
        return "ADJ"
    if value.startswith("RB"):
        return "ADV"
    if value in {"MD", "AUX"}:
        return "AUX"
    if value.startswith("PRP"):
        return "PRON"
    return None


def _selectors(token: LinguisticToken, context: ContextResolution | None) -> tuple[str, ...]:
    values: list[str] = []
    if token.tag:
        values.append(token.tag)
    pos = token.pos or _tag_pos(token.tag)
    if pos:
        values.append(pos)
    if context:
        values.extend(
            (
                context.selector,
                context.selector.replace("SENSE_", "SENSE:"),
                context.selector.removeprefix("SENSE_"),
            )
        )
    values.append("DEFAULT")
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return tuple(result)


def _case_variants(word: str) -> tuple[str, ...]:
    values = (word, word.casefold(), word.lower(), word.title(), word.upper())
    return tuple(dict.fromkeys(values))


def _preserve_punctuation(source_text: str, generated: str) -> str:
    word_ranges = tuple((match.start(), match.end()) for match in _WORD_RE.finditer(source_text))
    expected: list[str] = []
    for position, character in enumerate(source_text):
        if character not in SYMBOL_TO_ID or character.isspace():
            continue
        if not any(start <= position < end for start, end in word_ranges):
            expected.append(character)
    counts: dict[str, int] = {}
    for character in generated:
        counts[character] = counts.get(character, 0) + 1
    seen: dict[str, int] = {}
    missing: list[str] = []
    for character in expected:
        seen[character] = seen.get(character, 0) + 1
        if seen[character] > counts.get(character, 0):
            missing.append(character)
    return generated + "".join(missing)


def _punctuation_after(text: str, offset: int) -> tuple[int, str]:
    end = offset
    marks: list[str] = []
    while end < len(text) and text[end] in _PUNCTUATION:
        marks.append(text[end])
        end += 1
    return end, "".join(marks)


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
        self._lexicon_sources: tuple[LoadedLexiconSource, ...] = ()
        try:
            self._lexicon_sources = open_g2lex_sources(
                self.config.language,
                self.config.g2lex_files,
                self.config.lexicons,
                self.config.lexicon_data_policy,
            )
        except Exception:
            if self._owns_backend:
                self.backend.close()
            self._closed = True
            raise

    def phonemize_prepared(
        self,
        text: str,
        *,
        tokens: (
            Sequence[LinguisticToken | Mapping[str, Any]]
            | LinguisticToken
            | Mapping[str, Any]
            | None
        ) = None,
        pronunciation_overrides: Sequence[PronunciationOverride | Mapping[str, Any]]
        | PronunciationOverride
        | Mapping[str, Any]
        | None = None,
    ) -> PhonemizeResult:
        """Phonemize prepared text with optional token context and IPA spans.

        The one-argument call preserves the original whole-request eSpeak path.
        Explicit spans take precedence over local sources, named sources, context
        rules, and eSpeak fallback.
        """
        if self._closed:
            raise RuntimeError("KittenG2P is closed")
        if not isinstance(text, str):
            raise TypeError("prepared text must be a string")
        if not self._lexicon_sources and tokens is None and pronunciation_overrides is None:
            return self._phonemize_legacy(text)

        aligned_tokens = _normalize_tokens(text, tokens)
        overrides = _normalize_overrides(
            text, pronunciation_overrides, self.config.language, aligned_tokens
        )
        if not self._lexicon_sources and not overrides and not tokens:
            return self._phonemize_legacy(text)

        choices: list[tuple[int, int, str, PronunciationTrace]] = []
        explicitly_covered: set[tuple[int, int]] = set()
        for override in overrides:
            value = _validate_ipa(
                override.phonemes, text[override.start : override.end], "explicit override"
            )
            choices.append(
                (
                    override.start,
                    override.end,
                    value,
                    PronunciationTrace(
                        text=text[override.start : override.end],
                        start=override.start,
                        end=override.end,
                        phonemes=value,
                        source="explicit",
                        selector=None,
                        reason="request-local pronunciation override has highest precedence",
                    ),
                )
            )
            explicitly_covered.update(
                (token.start, token.end)
                for token in aligned_tokens
                if override.start <= token.start and token.end <= override.end
            )

        for index, token in enumerate(aligned_tokens):
            if (token.start, token.end) in explicitly_covered:
                continue
            context = (
                resolve_english_heteronym(token, aligned_tokens, index, text=text)
                if self.config.heteronym_policy == "auto"
                else None
            )

            selected: tuple[LoadedLexiconSource, str, str | None] | None = None
            selector_order = _selectors(token, context)
            for source in self._lexicon_sources:
                for spelling in _case_variants(token.text):
                    hit = source.lookup(spelling, selector_order)
                    if hit is not None:
                        selected = (source, hit[0], hit[1])
                        break
                if selected is not None:
                    break
            if selected is not None:
                source, pronunciation, selector = selected
                pronunciation = _validate_ipa(pronunciation, token.text, source.source_name)
                reason = (
                    f"selected {selector} entry from {source.source_type} source"
                    if selector
                    else "unconditional pronunciation entry from selected source"
                )
                choices.append(
                    (
                        token.start,
                        token.end,
                        pronunciation,
                        PronunciationTrace(
                            text=token.text,
                            start=token.start,
                            end=token.end,
                            phonemes=pronunciation,
                            source=source.source_type,  # type: ignore[arg-type]
                            source_name=source.source_name,
                            sha256=source.content_sha256,
                            logical_sha256=source.logical_sha256,
                            selector=selector,
                            reason=reason,
                        ),
                    )
                )
            elif context is not None:
                pronunciation = _validate_ipa(context.phonemes, token.text, "context-rule")
                choices.append(
                    (
                        token.start,
                        token.end,
                        pronunciation,
                        PronunciationTrace(
                            text=token.text,
                            start=token.start,
                            end=token.end,
                            phonemes=pronunciation,
                            source="context-rule",
                            selector=context.selector,
                            reason=context.reason,
                        ),
                    )
                )

        replaced_spans = {(start, end) for start, end, _, _ in choices}
        traces: list[PronunciationTrace] = [trace for _, _, _, trace in choices]
        for token in aligned_tokens:
            span = (token.start, token.end)
            if span not in replaced_spans and span not in explicitly_covered:
                traces.append(
                    PronunciationTrace(
                        text=token.text,
                        start=token.start,
                        end=token.end,
                        phonemes="",
                        source="espeak",
                        reason=(
                            "no selected source or contextual rule supplied an applicable reading"
                        ),
                    )
                )

        if not choices:
            result = self._phonemize_legacy(text)
            return PhonemizeResult(
                text=result.text,
                raw_phonemes=result.raw_phonemes,
                phonemes=result.phonemes,
                token_ids=result.token_ids,
                language=result.language,
                dropped_symbols=result.dropped_symbols,
                pronunciation_trace=tuple(sorted(traces, key=lambda item: item.start)),
                diagnostics=result.diagnostics,
            )

        choices.sort(key=lambda item: item[0])
        pieces: list[str] = []
        cursor = 0
        for start, end, pronunciation, _trace in choices:
            fallback = text[cursor:start]
            if fallback.strip():
                generated = _preserve_punctuation(
                    fallback, self.backend.phonemize(fallback, language=self.config.language)
                )
                if generated:
                    pieces.append(generated)
            expanded_end, punctuation = _punctuation_after(text, end)
            pieces.append(pronunciation + punctuation)
            cursor = expanded_end
        fallback = text[cursor:]
        if fallback.strip():
            generated = _preserve_punctuation(
                fallback, self.backend.phonemize(fallback, language=self.config.language)
            )
            if generated:
                pieces.append(generated)
        raw = " ".join(piece for piece in pieces if piece)
        prepared = prepare_phoneme_text(raw)
        ids, dropped = encode_phonemes(prepared)
        return PhonemizeResult(
            text=text,
            raw_phonemes=raw,
            phonemes=prepared,
            token_ids=frame_token_ids(ids),
            language=self.config.language,
            dropped_symbols=dropped,
            pronunciation_trace=tuple(sorted(traces, key=lambda item: item.start)),
        )

    def _phonemize_legacy(self, text: str) -> PhonemizeResult:
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

    @property
    def pronunciation_identity(self) -> tuple[dict[str, str | None], ...]:
        """Ordered immutable source identities for diagnostics and downstream caching."""
        return tuple(
            {
                "selector": source.selector,
                "source_type": source.source_type,
                "asset_id": source.asset_id,
                "data_version": source.data_version,
                "path": source.source_path,
                "sha256": source.content_sha256,
                "logical_sha256": source.logical_sha256,
            }
            for source in self._lexicon_sources
        )

    def close(self) -> None:
        """Close the opened pronunciation sources and any owned backend."""
        if self._closed:
            return
        for source in reversed(self._lexicon_sources):
            source.close()
        self._lexicon_sources = ()
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
    tokens: (
        Sequence[LinguisticToken | Mapping[str, Any]] | LinguisticToken | Mapping[str, Any] | None
    ) = None,
    pronunciation_overrides: Sequence[PronunciationOverride | Mapping[str, Any]]
    | PronunciationOverride
    | Mapping[str, Any]
    | None = None,
) -> PhonemizeResult:
    """Phonemize prepared text with a temporary frontend.

    Optional linguistic tokens and explicit IPA spans use the same source
    resolution as :meth:`KittenG2P.phonemize_prepared`. The temporary frontend
    is closed before returning; injected backends remain caller-owned.
    """
    with KittenG2P(config, backend=backend) as g2p:
        return g2p.phonemize_prepared(
            text, tokens=tokens, pronunciation_overrides=pronunciation_overrides
        )


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
