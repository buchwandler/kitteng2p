from kitteng2p import KittenG2P

with KittenG2P() as g2p:
    result = g2p.phonemize_prepared("Hello, world.")

print("text:", result.text)
print("language:", result.language)
print("raw phonemes:", result.raw_phonemes)
print("prepared phonemes:", result.phonemes)
print("token IDs:", result.token_ids)
print("dropped symbols:", result.dropped_symbols)
