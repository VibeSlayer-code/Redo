from typer.testing import CliRunner

import main
from modules import preflight, storage


def test_preflight_detects_missing_tools(tmp_path, monkeypatch):
    monkeypatch.setattr(preflight.shutil, "which", lambda tool: None)

    result = preflight.run_preflight("dev", ["npm run dev"], root=tmp_path)

    assert result["code"] == 1
    assert "npm not found" in result["data"]["errors"]
    assert "node not found" in result["data"]["errors"]


def test_preflight_detects_missing_env_when_example_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(preflight.shutil, "which", lambda tool: f"/bin/{tool}")
    (tmp_path / ".env.example").write_text("TOKEN=\n", encoding="utf-8")

    result = preflight.run_preflight("test", ["echo ok"], root=tmp_path)

    assert result["code"] == 2
    assert ".env missing but .env.example exists" in result["data"]["warnings"]


def test_preflight_detects_missing_node_modules(tmp_path, monkeypatch):
    monkeypatch.setattr(preflight.shutil, "which", lambda tool: f"/bin/{tool}")
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")

    result = preflight.run_preflight("dev", ["npm run dev"], root=tmp_path)

    assert result["code"] == 2
    assert "package.json found" in result["data"]["passed"]
    assert "node_modules missing" in result["data"]["warnings"]


def test_preflight_detects_python_project_files(tmp_path, monkeypatch):
    monkeypatch.setattr(preflight.shutil, "which", lambda tool: f"/bin/{tool}")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")

    result = preflight.run_preflight("test", ["pytest"], root=tmp_path)

    assert result["code"] == 2
    assert "Python project file found" in result["data"]["passed"]
    assert ".venv missing" in result["data"]["warnings"]


def test_preflight_detects_cargo_project_files(tmp_path, monkeypatch):
    monkeypatch.setattr(preflight.shutil, "which", lambda tool: f"/bin/{tool}")
    (tmp_path / "Cargo.toml").write_text("[package]\nname='demo'\n", encoding="utf-8")

    result = preflight.run_preflight("build", ["cargo build"], root=tmp_path)

    assert result["code"] == 0
    assert "Cargo.toml found" in result["data"]["passed"]


def test_preflight_command_does_not_execute_workflow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflows.json")
    storage.add_workflow("hello", "Say hello", ["echo hello"])
    monkeypatch.setattr(
        main.runner,
        "run_workflow_commands",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("workflow should not run")),
    )
    cli = CliRunner()

    result = cli.invoke(main.app, ["preflight", "hello"])

    assert result.exit_code == 0
    assert "Preflight: hello" in result.output


def test_run_preflight_blocks_on_errors_without_confirmation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflows.json")
    storage.add_workflow("dev", "Run dev", ["npm run dev"])
    monkeypatch.setattr(
        main.runner,
        "run_workflow_commands",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("workflow should not run")),
    )
    cli = CliRunner()

    result = cli.invoke(main.app, ["run", "dev", "--preflight"], input="n\n")

    assert result.exit_code == 1
    assert "Preflight: dev" in result.output
    assert "workflow cancelled by user" in result.output
