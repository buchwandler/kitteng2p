from kitteng2p import KittenG2P


class FixedBackend:
    def phonemize(self, text: str, *, language: str) -> str:
        print("input:", text)
        print("language:", language)
        return "həˈloʊ"

    def close(self) -> None:
        print("caller owns this backend")


backend = FixedBackend()
with KittenG2P(backend=backend) as g2p:
    result = g2p.phonemize_prepared("Hello")

print(result.phonemes)
print(result.token_ids)
