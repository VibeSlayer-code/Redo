import tomllib
from pathlib import Path


def test_pyproject_defines_redo_console_script():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["scripts"]["redo"] == "main:app"
    assert "typer" in pyproject["project"]["dependencies"]
    assert "rich" in pyproject["project"]["dependencies"]
