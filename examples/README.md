# kitteng2p examples

These scripts demonstrate the public frontend, codec, and backend-injection
APIs. The first three examples need eSpeak available through the system or the
optional bundled runtime:

```console
python -m pip install "kitteng2p[bundled]"
```

Run examples from the repository root:

```console
python examples/basic_usage.py
python examples/result_inspection.py
python examples/backend_modes.py
python examples/custom_backend.py
python examples/codec_only.py
```

`custom_backend.py` and `codec_only.py` do not require a live eSpeak runtime.
