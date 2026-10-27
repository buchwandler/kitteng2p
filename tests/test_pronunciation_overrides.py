from __future__ import annotations

import pytest

from kitteng2p import (
    KittenG2P,
    KittenG2PConfig,
    LinguisticToken,
    PronunciationOverride,
)


class FakeBackend:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def phonemize(self, text: str, *, language: str) -> str:
        assert language == "en-us"
        self.calls.append(text)
        return "həloʊ"

    def close(self) -> None:
        pass


def test_explicit_span_overrides_context_and_keeps_punctuation():
    backend = FakeBackend()
    text = "Hello, bow!"
    start = text.index("bow")
    token = LinguisticToken(start, start + 3, "bow")
    override = PronunciationOverride(start, start + 3, "baʊ")

    with KittenG2P(KittenG2PConfig(), backend=backend) as g2p:
        result = g2p.phonemize_prepared(
            text,
            tokens=(token,),
            pronunciation_overrides=(override,),
        )

    assert result.raw_phonemes == "həloʊ, baʊ!"
    assert result.phonemes.count(",") == 1
    assert result.phonemes.count("!") == 1
    assert result.pronunciation_trace[-1].source == "explicit"
    assert result.pronunciation_trace[-1].text == "bow"
    assert backend.calls == ["Hello, "]
    assert result.token_ids[0] == 0
    assert result.token_ids[-2:] == (10, 0)


def test_invalid_offsets_overlap_and_unsupported_symbols_fail():
    with KittenG2P(backend=FakeBackend()) as g2p:
        with pytest.raises(ValueError, match="does not match source text"):
            g2p.phonemize_prepared(
                "bow",
                tokens=(LinguisticToken(0, 3, "bass"),),
            )
        with pytest.raises(ValueError, match="must cover one or more complete source words"):
            g2p.phonemize_prepared(
                "bow",
                pronunciation_overrides=(PronunciationOverride(1, 3, "baʊ"),),
            )
        with pytest.raises(ValueError, match="must not overlap"):
            g2p.phonemize_prepared(
                "bow bass",
                pronunciation_overrides=(
                    PronunciationOverride(0, 3, "baʊ"),
                    PronunciationOverride(2, 6, "bæs"),
                ),
            )
        with pytest.raises(ValueError, match="unsupported Kitten phoneme symbol"):
            g2p.phonemize_prepared(
                "bow",
                pronunciation_overrides=(PronunciationOverride(0, 3, "☃"),),
            )


def test_fallback_runs_keep_clause_punctuation_without_extra_sentence_marks():
    backend = FakeBackend()
    text = "Hello, bow!"
    start = text.index("bow")

    with KittenG2P(backend=backend) as g2p:
        result = g2p.phonemize_prepared(
            text,
            pronunciation_overrides=(PronunciationOverride(start, start + 3, "baʊ"),),
        )

    assert result.phonemes.count(",") == 1
    assert result.phonemes.count("!") == 1
    assert backend.calls == ["Hello, "]
