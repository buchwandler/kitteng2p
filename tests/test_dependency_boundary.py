from pathlib import Path
import tomllib


def test_core_dependencies_are_frontend_only():
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    deps = " ".join(data["project"]["dependencies"]).lower()
    assert "espeakng-runtime" in deps
    assert "onnxvoice" not in deps
    assert "kittensynth" not in deps
    assert "phonemizer" not in deps
