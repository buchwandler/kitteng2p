from pathlib import Path

from packaging.requirements import Requirement

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def test_distribution_metadata_contract():
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]

    assert project["name"] == "kitteng2p"
    assert project["requires-python"] == ">=3.10"
    assert project["dynamic"] == ["version"]
    assert data["tool"]["setuptools"]["package-data"]["kitteng2p"] == ["py.typed"]
    assert project["scripts"]["kitteng2p"] == "kitteng2p.__main__:main"

    runtime = [Requirement(value) for value in project["dependencies"]]
    espeak = next(requirement for requirement in runtime if requirement.name == "espeakng-runtime")
    assert str(espeak.specifier) == "<0.2,>=0.1.5"
