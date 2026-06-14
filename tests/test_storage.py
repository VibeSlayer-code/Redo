import json
from pathlib import Path

from modules import storage


def test_default_storage_file_lives_under_redo_files():
    assert storage.DATA_FILE == Path("C:/redo/files/workflows.json")


def test_initialize_file_creates_empty_json(tmp_path, monkeypatch):
    data_file = tmp_path / "workflow.json"
    monkeypatch.setattr(storage, "DATA_FILE", data_file)

    result = storage.initialize_file()

    assert result["code"] == 0
    assert result["status"] == "success"
    assert json.loads(data_file.read_text(encoding="utf-8")) == {}


def test_load_workflows_initializes_missing_file(tmp_path, monkeypatch):
    data_file = tmp_path / "workflow.json"
    monkeypatch.setattr(storage, "DATA_FILE", data_file)

    result = storage.load_workflows()

    assert result["code"] == 0
    assert result["data"] == {}
    assert data_file.exists()


def test_save_and_get_workflow_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflow.json")

    add_result = storage.add_workflow("ship", "Commit and push", ["git add .", "git push"])
    get_result = storage.get_workflow("ship")

    assert add_result["status"] == "success"
    assert get_result["data"] == {
        "description": "Commit and push",
        "commands": ["git add .", "git push"],
        "runs": 0,
    }


def test_add_workflow_rejects_duplicates(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflow.json")
    storage.add_workflow("ship", "First", ["git status"])

    result = storage.add_workflow("ship", "Second", ["git push"])

    assert result["code"] == 2
    assert result["status"] == "warning"


def test_add_workflow_rejects_blank_or_reserved_names(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflow.json")

    blank_result = storage.add_workflow("   ", "Bad", ["echo bad"])
    reserved_result = storage.add_workflow("run", "Bad", ["echo bad"])

    assert blank_result["code"] == 2
    assert "workflow name" in blank_result["message"]
    assert reserved_result["code"] == 2
    assert "reserved" in reserved_result["message"]


def test_delete_workflow_removes_existing_workflow(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflow.json")
    storage.add_workflow("clean", "Clean build output", ["rm -rf dist"])

    delete_result = storage.delete_workflow("clean")
    get_result = storage.get_workflow("clean")

    assert delete_result["status"] == "success"
    assert get_result["code"] == 2


def test_increment_runs_updates_count_and_message(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflow.json")
    storage.add_workflow("test", "Run tests", ["pytest"])

    result = storage.increment_runs("test")

    assert result == {
        "code": 0,
        "status": "success",
        "message": "workflow run count updated",
    }
    assert storage.get_workflow("test")["data"]["runs"] == 1


def test_copy_workflow_duplicates_existing_workflow(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflow.json")
    storage.add_workflow("ship", "Commit and push", ["git push"])

    result = storage.copy_workflow("ship", "deploy")

    assert result["status"] == "success"
    assert storage.get_workflow("deploy")["data"] == {
        "description": "Commit and push",
        "commands": ["git push"],
        "runs": 0,
    }


def test_rename_workflow_moves_existing_workflow(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflow.json")
    storage.add_workflow("old", "Run checks", ["pytest"])

    result = storage.rename_workflow("old", "checks")

    assert result["status"] == "success"
    assert storage.get_workflow("old")["code"] == 2
    assert storage.get_workflow("checks")["data"]["commands"] == ["pytest"]


def test_copy_and_rename_reject_reserved_target_names(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflow.json")
    storage.add_workflow("ship", "Commit and push", ["git push"])

    copy_result = storage.copy_workflow("ship", "run")
    rename_result = storage.rename_workflow("ship", "delete")

    assert copy_result["code"] == 2
    assert rename_result["code"] == 2


def test_find_workflows_matches_name_description_and_commands(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflow.json")
    storage.add_workflow("ship", "Commit and push", ["git push"])
    storage.add_workflow("setup", "Install dependencies", ["pip install -r requirements.txt"])

    result = storage.find_workflows("install")

    assert result["code"] == 0
    assert list(result["data"].keys()) == ["setup"]


def test_export_and_import_workflows(tmp_path, monkeypatch):
    data_file = tmp_path / "workflow.json"
    export_file = tmp_path / "backup.json"
    monkeypatch.setattr(storage, "DATA_FILE", data_file)
    storage.add_workflow("ship", "Commit and push", ["git push"])

    export_result = storage.export_workflows(export_file)
    storage.delete_workflow("ship")
    import_result = storage.import_workflows(export_file)

    assert export_result["status"] == "success"
    assert import_result["status"] == "success"
    assert storage.get_workflow("ship")["data"]["commands"] == ["git push"]


def test_import_skips_reserved_and_invalid_workflow_names(tmp_path, monkeypatch):
    data_file = tmp_path / "workflow.json"
    import_file = tmp_path / "import.json"
    monkeypatch.setattr(storage, "DATA_FILE", data_file)
    import_file.write_text(
        json.dumps(
            {
                "run": {"description": "reserved", "commands": ["echo bad"], "runs": 0},
                "   ": {"description": "blank", "commands": ["echo bad"], "runs": 0},
                "ship": {"description": "valid", "commands": ["git push"], "runs": "bad"},
            }
        ),
        encoding="utf-8",
    )

    result = storage.import_workflows(import_file)

    workflows = storage.load_workflows()["data"]
    assert result["status"] == "success"
    assert set(workflows) == {"ship"}
    assert workflows["ship"]["runs"] == 0


def test_clear_workflows_resets_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflows.json")
    storage.add_workflow("ship", "Commit and push", ["git push"])

    result = storage.clear_workflows()

    assert result["status"] == "success"
    assert storage.load_workflows()["data"] == {}


def test_first_run_guide_state_lives_next_to_workflows(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "workflows.json")

    assert storage.should_offer_first_run_guide() is True
    result = storage.mark_first_run_guide_seen()

    assert result["status"] == "success"
    assert storage.should_offer_first_run_guide() is False
    assert (tmp_path / "redo_state.json").exists()


def test_malformed_json_returns_warning(tmp_path, monkeypatch):
    data_file = tmp_path / "workflow.json"
    data_file.write_text("{bad json", encoding="utf-8")
    monkeypatch.setattr(storage, "DATA_FILE", data_file)

    result = storage.load_workflows()

    assert result["code"] == 2
    assert result["status"] == "warning"
    assert result["data"] == {}


def test_autofix_creates_missing_workflow_file(tmp_path, monkeypatch):
    data_file = tmp_path / "workflows.json"
    monkeypatch.setattr(storage, "DATA_FILE", data_file)

    result = storage.autofix_storage()

    assert result["code"] == 0
    assert json.loads(data_file.read_text(encoding="utf-8")) == {}
    assert "created workflow file" in result["data"]["fixes"]


def test_autofix_backs_up_malformed_json_and_resets_file(tmp_path, monkeypatch):
    data_file = tmp_path / "workflows.json"
    data_file.write_text("{bad json", encoding="utf-8")
    monkeypatch.setattr(storage, "DATA_FILE", data_file)

    result = storage.autofix_storage()

    backup_file = tmp_path / "workflows.broken.json"
    assert result["code"] == 0
    assert backup_file.exists()
    assert json.loads(data_file.read_text(encoding="utf-8")) == {}
    assert "backed up malformed workflow file" in result["data"]["fixes"]


def test_autofix_normalizes_invalid_workflow_entries(tmp_path, monkeypatch):
    data_file = tmp_path / "workflows.json"
    data_file.write_text(
        json.dumps(
            {
                "ship": {"commands": "git push", "runs": "2"},
                "broken": "not a workflow",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(storage, "DATA_FILE", data_file)

    result = storage.autofix_storage()

    fixed = json.loads(data_file.read_text(encoding="utf-8"))
    assert result["code"] == 0
    assert fixed == {
        "ship": {
            "description": "",
            "commands": ["git push"],
            "runs": 2,
        }
    }


def test_autofix_removes_reserved_workflow_names(tmp_path, monkeypatch):
    data_file = tmp_path / "workflows.json"
    data_file.write_text(
        json.dumps(
            {
                "run": {"description": "Reserved", "commands": ["echo bad"], "runs": 0},
                "ship": {"description": "Valid", "commands": "git push", "runs": "3"},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(storage, "DATA_FILE", data_file)

    result = storage.autofix_storage()

    fixed = json.loads(data_file.read_text(encoding="utf-8"))
    assert result["code"] == 0
    assert fixed == {
        "ship": {
            "description": "Valid",
            "commands": ["git push"],
            "runs": 3,
        }
    }
