from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def _project_data():
    return tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))


def test_core_dependencies_are_frontend_only():
    data = _project_data()
    deps = " ".join(data["project"]["dependencies"]).lower()
    assert "espeakng-runtime" in deps
    assert "onnxvoice" not in deps
    assert "kittensynth" not in deps
    assert "phonemizer" not in deps
    assert "numpy" not in deps


def test_optional_extras_do_not_add_model_or_audio_dependencies():
    data = _project_data()
    optional = " ".join(
        requirement
        for requirements in data["project"]["optional-dependencies"].values()
        for requirement in requirements
    ).lower()

    assert "onnxvoice" not in optional
    assert "kittensynth" not in optional
    assert "phonemizer" not in optional
    assert "numpy" not in optional
    bundled = data["project"]["optional-dependencies"]["bundled"]
    assert any(requirement.startswith("espeakng-runtime[bundled]") for requirement in bundled)
