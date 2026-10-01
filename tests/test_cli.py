import json

import pytest

from kitteng2p import KittenG2P
from kitteng2p import __main__ as cli


class FakeBackend:
    def phonemize(self, text: str, *, language: str) -> str:
        return "hə🙂"

    def close(self) -> None:
        raise AssertionError("injected backend must remain caller-owned")


def test_cli_emits_unicode_json_and_uses_default_language(monkeypatch, capsys):
    configs = []

    def frontend_factory(config):
        configs.append(config)
        return KittenG2P(config, backend=FakeBackend())

    monkeypatch.setattr(cli, "KittenG2P", frontend_factory)

    assert cli.main(["Hello🙂"]) == 0

    output = capsys.readouterr().out
    result = json.loads(output)
    assert "🙂" in output
    assert result["text"] == "Hello🙂"
    assert result["dropped_symbols"] == ["🙂"]
    assert configs[0].language == "en-us"
    assert configs[0].espeak_mode == "auto"


def test_cli_accepts_language_and_backend_mode(monkeypatch, capsys):
    configs = []

    def frontend_factory(config):
        configs.append(config)
        return KittenG2P(config, backend=FakeBackend())

    monkeypatch.setattr(cli, "KittenG2P", frontend_factory)

    assert cli.main(["--language", "en-gb", "--espeak-mode", "cli", "hello"]) == 0
    capsys.readouterr()
    assert configs[0].language == "en-gb"
    assert configs[0].espeak_mode == "cli"


def test_cli_help_exits_successfully(capsys):
    with pytest.raises(SystemExit) as error:
        cli.main(["--help"])

    assert error.value.code == 0
    assert "--espeak-mode" in capsys.readouterr().out


def test_cli_rejects_invalid_backend_mode(capsys):
    with pytest.raises(SystemExit) as error:
        cli.main(["--espeak-mode", "invalid", "hello"])

    assert error.value.code == 2
    assert "invalid choice" in capsys.readouterr().err
