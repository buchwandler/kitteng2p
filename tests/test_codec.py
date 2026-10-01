from kitteng2p.codec import (
    FRAME_SUFFIX_IDS,
    SYMBOL_TO_ID,
    encode_phonemes,
    frame_token_ids,
    prepare_phoneme_text,
)


def test_upstream_duplicate_quote_keeps_last_index():
    assert SYMBOL_TO_ID['"'] > 1


def test_basic_prepare_and_frame():
    prepared = prepare_phoneme_text("həˈloʊ, wɜːld!")
    assert prepared == "həˈloʊ , wɜːld !"
    ids, dropped = encode_phonemes(prepared)
    assert dropped == ()
    framed = frame_token_ids(ids)
    assert framed[0] == 0
    assert framed[-2:] == FRAME_SUFFIX_IDS


def test_unknown_symbols_are_dropped_like_upstream():
    ids, dropped = encode_phonemes("a🙂b")
    assert len(ids) == 2
    assert dropped == ("🙂",)
