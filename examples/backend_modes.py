import argparse

from kitteng2p import KittenG2P, KittenG2PConfig

parser = argparse.ArgumentParser()
parser.add_argument("text", nargs="?", default="Hello world")
parser.add_argument("--mode", choices=("auto", "native", "cli"), default="auto")
parser.add_argument("--language", default="en-us")
args = parser.parse_args()

config = KittenG2PConfig(language=args.language, espeak_mode=args.mode)
with KittenG2P(config) as g2p:
    result = g2p.phonemize_prepared(args.text)

print(result.phonemes)
print(result.token_ids)
