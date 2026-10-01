import pytest

from kitteng2p.codec import (
    FRAME_PREFIX_ID,
    FRAME_SUFFIX_IDS,
    SYMBOL_TO_ID,
    SYMBOLS,
    encode_phonemes,
    frame_token_ids,
    prepare_phoneme_text,
)


def test_frame_constants_match_upstream_values():
    assert FRAME_PREFIX_ID == 0
    assert FRAME_SUFFIX_IDS == (10, 0)


def test_symbol_inventory_size_is_stable():
    assert len(SYMBOLS) == 178


@pytest.mark.parametrize(
    ("symbol", "expected"),
    [
        ("$", 0),
        (" ", 16),
        ('"', 15),
        ("a", 43),
        ("ˈ", 156),
        ("ə", 83),
        ("̩", 175),
    ],
)
def test_known_symbol_ids(symbol: str, expected: int):
    assert SYMBOL_TO_ID[symbol] == expected


def test_basic_prepare_and_frame():
    prepared = prepare_phoneme_text("həˈloʊ, wɜːld!")
    assert prepared == "həˈloʊ , wɜːld !"
    ids, dropped = encode_phonemes(prepared)
    assert dropped == ()

    framed = frame_token_ids(ids)
    assert framed[0] == FRAME_PREFIX_ID
    assert framed[-2:] == FRAME_SUFFIX_IDS


def test_unknown_symbols_are_dropped_like_upstream():
    ids, dropped = encode_phonemes("a🙂b🙂")
    assert len(ids) == 2
    assert dropped == ("🙂", "🙂")


def test_empty_phonemes_frame_to_prefix_and_suffix():
    assert frame_token_ids(()) == (0, 10, 0)
