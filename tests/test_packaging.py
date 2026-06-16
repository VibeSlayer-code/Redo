import tomllib
from pathlib import Path

import main


def test_pyproject_defines_redo_console_script():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["scripts"]["redo"] == "main:app"
    dependencies = pyproject["project"]["dependencies"]
    assert any(dependency.startswith("typer") for dependency in dependencies)
    assert any(dependency.startswith("rich") for dependency in dependencies)
    assert pyproject["project"]["authors"] == [{"name": "Vibeslayer-code"}]


def test_main_version_matches_pyproject_version():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert main.VERSION == pyproject["project"]["version"]


def test_contributor_docs_exist_and_are_linked_from_readme():
    readme = Path("README.md").read_text(encoding="utf-8")
    docs = Path("docs.md").read_text(encoding="utf-8")

    assert "docs.md" in readme
    assert "Contributor Guide" in docs
    assert "Architecture" in docs
