from kitteng2p import encode_phonemes, frame_token_ids, prepare_phoneme_text

raw = "həˈloʊ, wɜːld!"
prepared = prepare_phoneme_text(raw)
ids, dropped = encode_phonemes(prepared)
framed = frame_token_ids(ids)

print("raw:", raw)
print("prepared:", prepared)
print("ids:", ids)
print("framed:", framed)
print("dropped:", dropped)
