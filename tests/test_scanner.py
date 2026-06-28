import json

from typer.testing import CliRunner

import main
from modules import scanner, storage


def test_node_project_detection_from_package_json(tmp_path):
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"dev": "vite", "build": "vite build", "test": "vitest"}}),
        encoding="utf-8-sig",
    )

    result = scanner.detect_project(tmp_path)

    assert result["code"] == 0
    assert result["data"]["type"] == "Node"
    assert result["data"]["workflows"]["dev"]["commands"] == ["npm run dev"]
    assert result["data"]["workflows"]["build"]["commands"] == ["npm run build"]
    assert result["data"]["workflows"]["test"]["commands"] == ["npm test"]


def test_python_project_detection_from_requirements(tmp_path):
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")

    result = scanner.detect_project(tmp_path)

    assert result["code"] == 0
    assert result["data"]["type"] == "Python"
    assert result["data"]["workflows"]["install"]["commands"] == ["pip install -r requirements.txt"]


def test_rust_project_detection_from_cargo_toml(tmp_path):
    (tmp_path / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")

    result = scanner.detect_project(tmp_path)

    assert result["code"] == 0
    assert result["data"]["type"] == "Rust"
    assert result["data"]["workflows"]["build"]["commands"] == ["cargo build"]


def test_setup_dry_does_not_write_project_workflows(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "global" / "workflows.json")
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    cli = CliRunner()

    result = cli.invoke(main.app, ["setup", "--dry"])

    assert result.exit_code == 0
    assert "Detected Python project" in result.output
    assert not (tmp_path / ".redo" / "workflows.json").exists()


def test_setup_yes_writes_project_workflows(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "global" / "workflows.json")
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    cli = CliRunner()

    result = cli.invoke(main.app, ["setup", "--yes"])

    workflows = storage.load_workflows_from(tmp_path / ".redo" / "workflows.json")["data"]
    assert result.exit_code == 0
    assert "project workflows updated" in result.output
    assert "install" in workflows
    assert workflows["test"]["commands"] == ["pytest"]


def test_setup_does_not_overwrite_existing_workflows_without_confirmation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "global" / "workflows.json")
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    project_file = tmp_path / ".redo" / "workflows.json"
    storage.save_workflows_to(project_file, {"test": {"description": "Custom", "commands": ["python custom.py"], "runs": 4}})
    cli = CliRunner()

    result = cli.invoke(main.app, ["setup"], input="y\nn\n")

    workflows = storage.load_workflows_from(project_file)["data"]
    assert result.exit_code == 0
    assert workflows["test"]["commands"] == ["python custom.py"]
    assert "test" in result.output
