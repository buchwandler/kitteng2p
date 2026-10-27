from __future__ import annotations

from typing import Any

import pytest

from kitteng2p import KittenG2P, LinguisticToken, PronunciationOverride
from kitteng2p.api import _normalize_tokens


class FakeBackend:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def phonemize(self, text: str, *, language: str) -> str:
        assert language == "en-us"
        self.calls.append(text)
        return "fə"

    def close(self) -> None:
        pass


def test_punctuation_tokens_are_ignored_as_annotations_but_preserve_word_context():
    text = "Hello, bow!"
    tokens = (
        LinguisticToken(0, 5, "Hello", pos="INTJ"),
        LinguisticToken(5, 6, ",", pos="PUNCT"),
        LinguisticToken(7, 10, "bow", pos="NOUN"),
        LinguisticToken(10, 11, "!", pos="PUNCT"),
    )

    words = _normalize_tokens(text, tokens)

    assert [(word.start, word.end, word.text) for word in words] == [
        (0, 5, "Hello"),
        (7, 10, "bow"),
    ]
    assert words[0].pos == "INTJ"
    assert words[1].pos == "NOUN"

    backend = FakeBackend()
    with KittenG2P(backend=backend) as g2p:
        result = g2p.phonemize_prepared(
            text,
            tokens=tokens,
            pronunciation_overrides=(PronunciationOverride(7, 10, "baʊ"),),
        )

    assert result.phonemes.count(",") == 1
    assert result.phonemes.count("!") == 1
    assert [(item.start, item.end) for item in result.pronunciation_trace] == [(0, 5), (7, 10)]


def test_punctuation_attached_hints_project_to_internal_words_without_attached_text():
    text = "Hello, bow!"
    tokens = (
        LinguisticToken(0, 6, "Hello,", pos="INTJ", lemma="hello"),
        LinguisticToken(7, 11, "bow!", pos="NOUN", tag="NN", lemma="bow", morph="Number=Sing"),
    )

    words = _normalize_tokens(text, tokens)

    assert [(word.start, word.end, word.text) for word in words] == [
        (0, 5, "Hello"),
        (7, 10, "bow"),
    ]
    assert words[0].pos == "INTJ"
    assert words[0].lemma is None
    assert words[1].pos == "NOUN"
    assert words[1].tag == "NN"
    assert words[1].morph == "Number=Sing"
    assert words[1].lemma is None

    with KittenG2P(backend=FakeBackend()) as g2p:
        result = g2p.phonemize_prepared(
            text,
            tokens=tokens,
            pronunciation_overrides=(PronunciationOverride(7, 10, "baʊ"),),
        )
    assert [item.text for item in result.pronunciation_trace] == ["Hello", "bow"]
    assert result.phonemes.count(",") == 1
    assert result.phonemes.count("!") == 1


def test_exact_heteronym_annotation_survives_surrounding_punctuation():
    text = "The refuse was collected."
    start = text.index("refuse")
    tokens = (
        LinguisticToken(0, 3, "The", pos="DET"),
        LinguisticToken(start, start + 6, "refuse", pos="NOUN", tag="NN", lemma="refuse"),
        LinguisticToken(11, 14, "was", pos="AUX"),
        LinguisticToken(15, 24, "collected", pos="VERB"),
        LinguisticToken(24, 25, ".", pos="PUNCT"),
    )

    words = _normalize_tokens(text, tokens)
    assert words[1].pos == "NOUN"
    assert words[1].tag == "NN"
    assert words[1].lemma == "refuse"

    with KittenG2P(backend=FakeBackend()) as g2p:
        result = g2p.phonemize_prepared(text, tokens=tokens)
    trace = next(item for item in result.pronunciation_trace if item.text == "refuse")
    assert trace.source == "context-rule"
    assert trace.selector == "SENSE_NOUN"
    assert (trace.start, trace.end) == (start, start + 6)
    assert result.phonemes.count(".") == 1


def test_contraction_fragments_are_ignored_but_exact_word_hint_remains_usable():
    text = "I can't refuse."
    start = text.index("refuse")
    tokens = (
        LinguisticToken(0, 1, "I", pos="PRON"),
        LinguisticToken(2, 4, "ca", pos="AUX"),
        LinguisticToken(4, 7, "n't", pos="PART"),
        LinguisticToken(start, start + 6, "refuse", pos="VERB", tag="VB", lemma="refuse"),
        LinguisticToken(14, 15, ".", pos="PUNCT"),
    )

    words = _normalize_tokens(text, tokens)
    assert [(word.text, word.pos) for word in words] == [
        ("I", "PRON"),
        ("can't", None),
        ("refuse", "VERB"),
    ]
    with KittenG2P(backend=FakeBackend()) as g2p:
        result = g2p.phonemize_prepared(text, tokens=tokens)
    assert any(item.text == "refuse" for item in result.pronunciation_trace)
    assert result.phonemes.count(".") == 1


def test_multiword_hint_does_not_redefine_internal_word_segmentation():
    text = "New York"
    words = _normalize_tokens(text, (LinguisticToken(0, len(text), text, pos="PROPN"),))

    assert [(word.start, word.end, word.text, word.pos) for word in words] == [
        (0, 3, "New", None),
        (4, 8, "York", None),
    ]
    with KittenG2P(backend=FakeBackend()) as g2p:
        result = g2p.phonemize_prepared(text, tokens=(LinguisticToken(0, 8, text, pos="PROPN"),))
    assert [item.text for item in result.pronunciation_trace] == ["New", "York"]


def test_source_mismatch_out_of_bounds_and_overlapping_hints_still_fail():
    with pytest.raises(ValueError, match="does not match source text"):
        _normalize_tokens("bow", (LinguisticToken(0, 3, "bass"),))

    with pytest.raises(ValueError, match="exceeds text length"):
        _normalize_tokens("bow", (LinguisticToken(0, 4, "bows"),))

    with pytest.raises(ValueError, match="must not overlap"):
        _normalize_tokens(
            "abc",
            (LinguisticToken(0, 2, "ab"), LinguisticToken(1, 3, "bc")),
        )

    with pytest.raises(ValueError, match="monotonic"):
        _normalize_tokens(
            "bow bass",
            (LinguisticToken(4, 8, "bass"), LinguisticToken(0, 3, "bow")),
        )


def test_non_integer_offsets_are_rejected():
    with pytest.raises(TypeError, match="offsets must be integers"):
        invalid_start: Any = 0.5
        LinguisticToken(invalid_start, 2, "ab")
