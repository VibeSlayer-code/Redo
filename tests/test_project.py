import json

from typer.testing import CliRunner

import main
from modules import project, storage


def test_init_project_creates_project_workflow_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "global" / "workflows.json")
    cli = CliRunner()

    result = cli.invoke(main.app, ["init", "--project"])

    project_file = tmp_path / ".redo" / "workflows.json"
    assert result.exit_code == 0
    assert project_file.exists()
    assert json.loads(project_file.read_text(encoding="utf-8")) == {}


def test_project_workflows_win_before_global_workflows(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "global" / "workflows.json")
    storage.add_workflow("dev", "Global dev", ["echo global"])
    project_file = tmp_path / ".redo" / "workflows.json"
    storage.save_workflows_to(project_file, {"dev": {"description": "Project dev", "commands": ["echo project"], "runs": 0}})

    result = project.get_visible_workflow("dev")

    assert result["code"] == 0
    assert result["data"]["source"] == "project"
    assert result["data"]["workflow"]["commands"] == ["echo project"]


def test_global_workflows_still_work_without_project_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "global" / "workflows.json")
    storage.add_workflow("ship", "Global ship", ["git push"])
    cli = CliRunner()

    result = cli.invoke(main.app, ["show", "ship"])

    assert result.exit_code == 0
    assert "Global ship" in result.output
    assert "global" in result.output


def test_path_project_prints_project_workflow_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "global" / "workflows.json")
    cli = CliRunner()

    result = cli.invoke(main.app, ["path", "--project"])

    assert result.exit_code == 0
    assert str((tmp_path / ".redo" / "workflows.json").resolve()) in result.output
