# kitteng2p

Independent phoneme and token-ID frontend targeting the public KittenTTS v0.8
text-cleaner contract.

`kitteng2p` turns prepared, speakable text into eSpeak phonemes, Kitten-prepared
phoneme text, character IDs, and model framing `(0, *ids, 10, 0)`. It does not
synthesize audio, load ONNX models, download voices, or perform written-to-spoken
semantic normalization. Callers prepare dates, currencies, units, URLs, and
abbreviations before phonemization.

The package has a flat layout and uses `setuptools-scm` for dynamic versioning.

## Installation

Install `kitteng2p` and make a system eSpeak or eSpeak NG runtime available to
`espeakng-runtime`:

```console
python -m pip install kitteng2p
```

Where supported, install the optional bundled runtime assets instead:

```console
python -m pip install "kitteng2p[bundled]"
```

The `bundled` extra provisions eSpeak runtime assets where supported. It does
not install KittenTTS, a TTS model, or audio dependencies.

## Quick start

```python
from kitteng2p import KittenG2P

with KittenG2P() as g2p:
    result = g2p.phonemize_prepared("Hello, world.")

print(result.phonemes)
print(result.token_ids)
print(result.dropped_symbols)
```

The result's `token_ids` already include model framing. The convenience
functions `phonemes()` and `phoneme_ids()` create and close a temporary frontend.

## Command line

```console
kitteng2p "Hello, world."
kitteng2p --language en-gb "Hello, world."
kitteng2p --espeak-mode cli "Hello, world."
```

The command prints one JSON object with the original text, prepared phonemes,
framed token IDs, and any dropped symbols.

## Kitten v0.8 compatibility target

`kitteng2p` reproduces the public KittenTTS v0.8 text-cleaner symbol inventory
and model-ID framing:

- the same pad, punctuation, ASCII-letter, and IPA symbol inventory;
- duplicate symbols use the last dictionary index, matching upstream construction;
- symbols outside the inventory are dropped;
- model IDs are framed as `(0, *ids, 10, 0)`.

This is a codec-level compatibility claim. The released KittenTTS 0.8.1 path
uses `phonemizer` around eSpeak, while `kitteng2p` uses `espeakng-runtime`.
Exact sentence-level ID parity has not been established across a representative
corpus. Do not interpret codec compatibility as end-to-end phonemizer parity.
See the [compatibility policy](docs/compatibility.md).

## Documentation

- [Installation](docs/installation.md)
- [Quick start](docs/quickstart.md)
- [API reference](docs/api.md)
- [Codec contract](docs/codec.md)
- [eSpeak backend](docs/backends.md)
- [Command line](docs/cli.md)
- [Compatibility policy](docs/compatibility.md)
- [Architecture](docs/architecture.md)
- [Changelog](docs/changelog.md)
- [Runnable examples](examples/README.md)

## Dynamic versioning

Package versions are derived from Git tags through `setuptools-scm`. Source
archives without Git metadata use the configured `0.1.dev0` fallback. Create a
release tag only after the release checklist and artifact gates have passed.
At runtime, `kitteng2p.__version__` reports the installed distribution version.

## Development

```console
python -m pip install -e ".[dev,docs]"
python -m pytest
python -m ruff check kitteng2p tests examples
python -m mypy kitteng2p
python -m compileall -q kitteng2p tests tools examples
python docs/make.py html
python -m build --sdist --wheel
```
