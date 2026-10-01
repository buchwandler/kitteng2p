# Command line

The package installs a `kitteng2p` command.

## Basic use

```console
kitteng2p "Hello, world."
```

The command prints one JSON object. Its fields are `text`, prepared
`phonemes`, framed `token_ids`, and `dropped_symbols`. Actual phonemes and IDs
depend on the selected eSpeak runtime and voice.

## Language

```console
kitteng2p --language en-gb "Hello world"
```

## Backend mode

```console
kitteng2p --espeak-mode native "Hello world"
kitteng2p --espeak-mode cli "Hello world"
```

The default is `--espeak-mode auto`.
