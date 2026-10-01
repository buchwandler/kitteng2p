# kitteng2p

Independent KittenTTS-compatible phoneme and token-ID frontend.

This repository follows the same packaging conventions as `piperg2p`:

```text
pyproject.toml
kitteng2p/
tests/
docs/
```

There is **no `src/` layer**. Versioning is dynamic through Git tags and `setuptools-scm`.

## Scope

`kitteng2p` owns:

```text
prepared English text
  -> eSpeak NG IPA
  -> Kitten basic-English phoneme tokenization
  -> Kitten v0.8 character IDs
  -> upstream-compatible framing: [0] + ids + [10, 0]
```

It does **not**:

- synthesize audio;
- load ONNX models;
- download voices;
- normalize written semantics such as currencies/dates/URLs;
- depend on `onnxvoice` or `kittensynth`.

That semantic boundary intentionally matches `piperg2p`: callers pass already speakable text.

## Install

```bash
pip install kitteng2p
```

For the optional bundled eSpeak loader:

```bash
pip install "kitteng2p[bundled]"
```

## Quick start

```python
from kitteng2p import KittenG2P

with KittenG2P() as g2p:
    result = g2p.phonemize_prepared("Hello, world.")
    print(result.phonemes)
    print(result.token_ids)
```

Convenience API:

```python
from kitteng2p import phoneme_ids, phonemes

print(phonemes("Hello world"))
print(phoneme_ids("Hello world"))
```

## Kitten v0.8 compatibility

The codec is derived from the public KittenTTS v0.8 `TextCleaner` contract:

- identical `$` pad symbol;
- identical punctuation string;
- identical ASCII letter set;
- identical IPA symbol inventory;
- duplicate symbols retain the **last** upstream dictionary index;
- unknown characters are dropped, matching upstream behavior;
- model framing is `(0, *ids, 10, 0)`.

The default backend uses `espeakng-runtime`, which centralizes native/CLI discovery. A backend can
be injected for deterministic compatibility tests.

## Dynamic versioning

Versions come from Git tags:

```bash
git tag v0.1.0
python -m build
```

`pyproject.toml` uses:

```toml
dynamic = ["version"]
```

and `setuptools-scm`. Source zips without `.git` metadata fall back to `0.1.dev0` so the MVP remains
buildable before it is committed.

At runtime:

```python
import kitteng2p
print(kitteng2p.__version__)
```

reads installed distribution metadata, like `piperg2p`.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check kitteng2p tests
python -m mypy kitteng2p
python -m build
```

## MVP follow-up

Before calling the implementation "exact upstream parity", add a golden suite that runs the same
sentences through the released KittenTTS 0.8.1 `phonemizer` path and this `espeakng-runtime` path,
then compares the final framed token IDs. The package API is designed so that parity fixes remain
inside the backend/codec boundary.
