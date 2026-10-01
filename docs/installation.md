# Installation

## Requirements

`kitteng2p` requires Python 3.10 or newer. Its default backend uses
`espeakng-runtime`, so eSpeak NG must be available through the host system or,
where supported, the optional bundled runtime assets.

## System eSpeak

Install the package:

```console
python -m pip install kitteng2p
```

Install eSpeak or eSpeak NG using your operating system's package manager.
`KittenG2P()` uses `espeak_mode="auto"` by default. The runtime prefers a
usable native library and can fall back to the eSpeak command-line executable.

## Bundled runtime assets

Where supported, install the optional loader:

```console
python -m pip install "kitteng2p[bundled]"
```

This installs the `espeakng-runtime[bundled]` dependency set. It supplies
eSpeak runtime assets on supported platforms. It does not install KittenTTS
models, voices, ONNX Runtime, or audio dependencies.

## Development

```console
python -m pip install -e ".[dev,docs]"
python -m pytest
python -m ruff check kitteng2p tests examples
python -m mypy kitteng2p
python -m build
```

Build the documentation with:

```console
python docs/make.py html
```
