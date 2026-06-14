from typer.testing import CliRunner

import main
from modules import storage


def test_root_command_shows_ascii_banner_instead_of_help_description():
    cli = CliRunner()

    result = cli.invoke(main.app, [])

    assert result.exit_code == 0
    assert "/$$$$$$$" in result.output
    assert "Usage:" not in result.output


def test_help_option_shows_custom_redo_help_menu():
    cli = CliRunner()

    result = cli.invoke(main.app, ["--help"])

    assert result.exit_code == 0
    assert "Redo command center" in result.output
    assert "Daily workflow" in result.output
    assert "Utilities" in result.output
    assert "Bookmarks for terminal workflows" in result.output
    assert "Usage:" not in result.output


def test_subcommand_help_still_works_after_custom_root_help():
    cli = CliRunner()

    result = cli.invoke(main.app, ["run", "--help"])

    assert result.exit_code == 0
    assert "Run a saved workflow" in result.output


def test_info_option_shows_banner_version_and_credit():
    cli = CliRunner()

    result = cli.invoke(main.app, ["--info"])

    assert result.exit_code == 0
    assert "/$$$$$$$" in result.output
    assert "Version" in result.output
    assert "credit-vibeslayer" in result.output


def test_list_empty_workflows(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflow.json")
    cli = CliRunner()

    result = cli.invoke(main.app, ["list"])

    assert result.exit_code == 0
    assert "No workflows saved yet." in result.output


def test_run_dry_preview_does_not_increment_runs(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflow.json")
    storage.add_workflow("hello", "Say hello", ["echo hello"])
    cli = CliRunner()

    result = cli.invoke(main.app, ["run", "hello", "--dry"])

    assert result.exit_code == 0
    assert "echo hello" in result.output
    assert storage.get_workflow("hello")["data"]["runs"] == 0


def test_copy_rename_search_and_path_commands(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflow.json")
    storage.add_workflow("ship", "Commit and push", ["git push"])
    cli = CliRunner()

    copy_result = cli.invoke(main.app, ["copy", "ship", "deploy"])
    rename_result = cli.invoke(main.app, ["rename", "deploy", "release"])
    search_result = cli.invoke(main.app, ["search", "release"])
    path_result = cli.invoke(main.app, ["path"])

    assert copy_result.exit_code == 0
    assert rename_result.exit_code == 0
    assert search_result.exit_code == 0
    assert "release" in search_result.output
    assert str(tmp_path / "workflow.json") in path_result.output


def test_export_import_and_doctor_commands(tmp_path, monkeypatch):
    data_file = tmp_path / "workflow.json"
    backup_file = tmp_path / "backup.json"
    monkeypatch.setattr(storage, "DATA_FILE", data_file)
    storage.add_workflow("danger", "Needs review", ["git reset --hard HEAD"])
    cli = CliRunner()

    export_result = cli.invoke(main.app, ["export", str(backup_file)])
    storage.delete_workflow("danger")
    import_result = cli.invoke(main.app, ["import", str(backup_file)])
    doctor_result = cli.invoke(main.app, ["doctor"])

    assert export_result.exit_code == 0
    assert import_result.exit_code == 0
    assert doctor_result.exit_code == 0
    assert "Dangerous commands" in doctor_result.output
    assert storage.get_workflow("danger")["code"] == 0


def test_autofix_command_repairs_storage_file(tmp_path, monkeypatch):
    data_file = tmp_path / "workflows.json"
    data_file.write_text("{bad json", encoding="utf-8")
    monkeypatch.setattr(storage, "DATA_FILE", data_file)
    cli = CliRunner()

    result = cli.invoke(main.app, ["autofix"])

    assert result.exit_code == 0
    assert "backed up malformed workflow file" in result.output
    assert storage.load_workflows()["data"] == {}


def test_clearhistory_command_resets_workflows(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflows.json")
    storage.add_workflow("git", "for pushing", ["git push"])
    cli = CliRunner()

    result = cli.invoke(main.app, ["clearhistory", "--yes"])

    assert result.exit_code == 0
    assert "workflow history cleared" in result.output
    assert storage.load_workflows()["data"] == {}


def test_guide_command_can_be_viewed_anytime(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflows.json")
    cli = CliRunner()

    result = cli.invoke(main.app, ["guide"])

    assert result.exit_code == 0
    assert "Redo guide" in result.output
    assert "{message}" in result.output
    assert "redo run ship" in result.output


def test_new_workflow_first_run_can_show_guide(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflows.json")
    cli = CliRunner()

    result = cli.invoke(
        main.app,
        ["new", "ship"],
        input="y\nCommit and push\ngit add .\ngit commit -m \"{message}\"\ngit push\n:done\n",
    )

    assert result.exit_code == 0
    assert "Redo guide" in result.output
    assert "workflow saved successfully" in result.output
    assert storage.should_offer_first_run_guide() is False


def test_new_workflow_first_run_can_skip_guide(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflows.json")
    cli = CliRunner()

    result = cli.invoke(
        main.app,
        ["new", "ship"],
        input="n\nCommit and push\ngit status\n:done\n",
    )

    assert result.exit_code == 0
    assert "Redo guide" not in result.output
    assert storage.should_offer_first_run_guide() is False


def test_new_workflow_rejects_reserved_name_before_prompts(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflows.json")
    cli = CliRunner()

    result = cli.invoke(main.app, ["new", "run"])

    assert result.exit_code == 0
    assert "reserved" in result.output
    assert "Description:" not in result.output
