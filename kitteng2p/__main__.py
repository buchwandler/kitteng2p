from __future__ import annotations

import argparse
import json

from .api import KittenG2P
from .config import KittenG2PConfig


def main(argv: list[str] | None = None) -> int:
    """Run the command-line frontend with optional argument injection for tests."""
    parser = argparse.ArgumentParser(description="Prepare KittenTTS v0.8 phonemes and token IDs")
    parser.add_argument("text")
    parser.add_argument("--language", default="en-us")
    parser.add_argument("--espeak-mode", choices=["auto", "native", "cli"], default="auto")
    args = parser.parse_args(argv)

    config = KittenG2PConfig(language=args.language, espeak_mode=args.espeak_mode)
    with KittenG2P(config) as g2p:
        result = g2p.phonemize_prepared(args.text)
    print(
        json.dumps(
            {
                "text": result.text,
                "phonemes": result.phonemes,
                "token_ids": result.token_ids,
                "dropped_symbols": result.dropped_symbols,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
