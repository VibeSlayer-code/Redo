import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path


STATE_FILE_NAME = "redo_state.json"
RESERVED_WORKFLOW_NAMES = {
    "autofix",
    "clearhistory",
    "copy",
    "delete",
    "doctor",
    "export",
    "guide",
    "help",
    "import",
    "info",
    "init",
    "list",
    "new",
    "path",
    "rename",
    "run",
    "search",
    "show",
    "stats",
}


def _user_data_dir():
    override = os.environ.get("REDO_DATA_DIR")
    if override:
        return Path(override).expanduser()
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Redo"
    return Path.home() / ".redo"


DATA_DIR = _user_data_dir()
DATA_FILE = DATA_DIR / "workflows.json"


def _result(code, status, message, data=None):
    result = {
        "code": code,
        "status": status,
        "message": message,
    }
    if data is not None:
        result["data"] = data
    return result


def _write_text_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as file:
            temp_path = Path(file.name)
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        temp_path.replace(path)
    except OSError:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise


def _write_json_file(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as file:
            temp_path = Path(file.name)
            json.dump(data, file, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        temp_path.replace(path)
    except OSError:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise


def _require_loaded_workflows(result, allow_warnings=False):
    if result["code"] == 1:
        return None, result
    if result["code"] == 2 and not allow_warnings:
        return None, _result(1, "error", "workflow storage is invalid; run `redo autofix` first")
    return result.get("data", {}), None


def _validate_workflow_name(name):
    clean_name = str(name).strip()
    if not clean_name:
        return None, _result(2, "warning", "workflow name cannot be blank")
    if clean_name.lower() in RESERVED_WORKFLOW_NAMES:
        return None, _result(2, "warning", "workflow name is reserved by a Redo command")
    return clean_name, None


def validate_workflow_name(name):
    _, error = _validate_workflow_name(name)
    if error:
        return error
    return _result(0, "success", "workflow name is valid")


def initialize_file():
    try:
        if DATA_FILE.exists() and DATA_FILE.read_text(encoding="utf-8").strip():
            return _result(2, "warning", "workflow file already exists")
        _write_text_file(DATA_FILE, "{}\n")
        return _result(0, "success", "workflow file initialized")
    except (OSError, UnicodeDecodeError) as error:
        return _result(1, "error", f"could not initialize workflow file: {error}")


def _broken_backup_file():
    candidate = DATA_FILE.with_name(f"{DATA_FILE.stem}.broken.json")
    if not candidate.exists():
        return candidate
    index = 1
    while True:
        candidate = DATA_FILE.with_name(f"{DATA_FILE.stem}.broken.{index}.json")
        if not candidate.exists():
            return candidate
        index += 1


def _state_file():
    return DATA_FILE.parent / STATE_FILE_NAME


def _normalize_workflow(name, workflow):
    if not isinstance(name, str) or not name.strip() or not isinstance(workflow, dict):
        return None

    commands = workflow.get("commands", [])
    if isinstance(commands, str):
        commands = [commands]
    elif isinstance(commands, list):
        commands = [str(command) for command in commands if str(command).strip()]
    else:
        commands = []

    try:
        runs = int(workflow.get("runs", 0))
    except (TypeError, ValueError):
        runs = 0

    return {
        "description": str(workflow.get("description", "")),
        "commands": commands,
        "runs": max(runs, 0),
    }


def _normalize_workflows(workflows):
    if not isinstance(workflows, dict):
        return {}

    normalized = {}
    for name, workflow in workflows.items():
        clean_name, name_error = _validate_workflow_name(name)
        if name_error:
            continue

        fixed_workflow = _normalize_workflow(clean_name, workflow)
        if fixed_workflow is not None:
            normalized[clean_name] = fixed_workflow

    return normalized


def autofix_storage():
    fixes = []

    try:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        return _result(1, "error", f"could not create Redo data directory: {error}")

    try:
        if not DATA_FILE.exists():
            _write_text_file(DATA_FILE, "{}\n")
            fixes.append("created workflow file")
            return _result(0, "success", "autofix completed", {"fixes": fixes})

        raw_text = DATA_FILE.read_text(encoding="utf-8")
        if not raw_text.strip():
            _write_text_file(DATA_FILE, "{}\n")
            fixes.append("reset blank workflow file")
            return _result(0, "success", "autofix completed", {"fixes": fixes})

        try:
            workflows = json.loads(raw_text)
        except json.JSONDecodeError:
            backup_file = _broken_backup_file()
            _write_text_file(backup_file, raw_text)
            _write_text_file(DATA_FILE, "{}\n")
            fixes.append("backed up malformed workflow file")
            fixes.append("reset workflow file")
            return _result(0, "success", "autofix completed", {"fixes": fixes})

        normalized = _normalize_workflows(workflows)
        if normalized != workflows:
            save_result = save_workflows(normalized)
            if save_result["code"] != 0:
                return save_result
            fixes.append("normalized workflow entries")
    except (OSError, UnicodeDecodeError) as error:
        return _result(1, "error", f"could not autofix workflow storage: {error}")

    if not fixes:
        fixes.append("no fixes needed")

    return _result(0, "success", "autofix completed", {"fixes": fixes})


def load_workflows():
    try:
        if not DATA_FILE.exists() or not DATA_FILE.read_text(encoding="utf-8").strip():
            init_result = initialize_file()
            if init_result["code"] == 1:
                return {**init_result, "data": {}}

        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError:
        return _result(2, "warning", "workflow file is malformed", {})
    except (OSError, UnicodeDecodeError) as error:
        return _result(1, "error", f"could not load workflows: {error}", {})

    if not isinstance(data, dict):
        return _result(2, "warning", "workflow file must contain a JSON object", {})

    return _result(0, "success", "workflows loaded successfully", data)


def save_workflows(workflows):
    if not isinstance(workflows, dict):
        return _result(1, "error", "workflows must be a dictionary")

    try:
        _write_json_file(DATA_FILE, workflows)
    except OSError as error:
        return _result(1, "error", f"could not save workflows: {error}")

    return _result(0, "success", "workflows saved successfully")


def clear_workflows():
    workflows, error = _require_loaded_workflows(load_workflows())
    if error:
        return error

    save_result = save_workflows({})
    if save_result["code"] != 0:
        return save_result

    return _result(0, "success", "workflow history cleared")


def should_offer_first_run_guide():
    state_file = _state_file()
    if not state_file.exists():
        return True

    try:
        with state_file.open("r", encoding="utf-8") as file:
            state = json.load(file)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return True

    return not bool(state.get("first_run_guide_seen", False))


def mark_first_run_guide_seen():
    state_file = _state_file()

    try:
        state = {}
        if state_file.exists() and state_file.read_text(encoding="utf-8").strip():
            with state_file.open("r", encoding="utf-8") as file:
                state = json.load(file)

        state["first_run_guide_seen"] = True
        _write_json_file(state_file, state)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as error:
        return _result(1, "error", f"could not update first-run guide state: {error}")

    return _result(0, "success", "first-run guide state updated")


def add_workflow(name, description, commands):
    name, name_error = _validate_workflow_name(name)
    if name_error:
        return name_error

    workflows, error = _require_loaded_workflows(load_workflows())
    if error:
        return error

    if name in workflows:
        return _result(2, "warning", "workflow already exists")

    workflows[name] = {
        "description": description,
        "commands": commands,
        "runs": 0,
    }

    save_result = save_workflows(workflows)
    if save_result["code"] != 0:
        return save_result

    return _result(0, "success", "workflow saved successfully")


def get_workflow(name):
    name = str(name).strip()
    workflows, error = _require_loaded_workflows(load_workflows())
    if error:
        return error

    workflow = workflows.get(name)
    if workflow is None:
        return _result(2, "warning", "workflow not found", None)

    return _result(0, "success", "workflow found", workflow)


def delete_workflow(name):
    name = str(name).strip()
    workflows, error = _require_loaded_workflows(load_workflows())
    if error:
        return error

    if name not in workflows:
        return _result(2, "warning", "workflow not found")

    del workflows[name]
    save_result = save_workflows(workflows)
    if save_result["code"] != 0:
        return save_result

    return _result(0, "success", "workflow deleted successfully")


def increment_runs(name):
    name = str(name).strip()
    workflows, error = _require_loaded_workflows(load_workflows())
    if error:
        return error

    if name not in workflows:
        return _result(2, "warning", "workflow not found")

    try:
        workflows[name]["runs"] = int(workflows[name].get("runs", 0)) + 1
    except (TypeError, ValueError):
        workflows[name]["runs"] = 1

    save_result = save_workflows(workflows)
    if save_result["code"] != 0:
        return save_result

    return _result(0, "success", "workflow run count updated")


def copy_workflow(source_name, target_name):
    source_name = str(source_name).strip()
    target_name, name_error = _validate_workflow_name(target_name)
    if name_error:
        return name_error

    workflows, error = _require_loaded_workflows(load_workflows())
    if error:
        return error

    if source_name not in workflows:
        return _result(2, "warning", "source workflow not found")
    if target_name in workflows:
        return _result(2, "warning", "target workflow already exists")

    workflows[target_name] = deepcopy(workflows[source_name])
    workflows[target_name]["runs"] = 0

    save_result = save_workflows(workflows)
    if save_result["code"] != 0:
        return save_result

    return _result(0, "success", "workflow copied successfully")


def rename_workflow(old_name, new_name):
    old_name = str(old_name).strip()
    new_name, name_error = _validate_workflow_name(new_name)
    if name_error:
        return name_error

    workflows, error = _require_loaded_workflows(load_workflows())
    if error:
        return error

    if old_name not in workflows:
        return _result(2, "warning", "workflow not found")
    if new_name in workflows:
        return _result(2, "warning", "target workflow already exists")

    workflows[new_name] = workflows.pop(old_name)

    save_result = save_workflows(workflows)
    if save_result["code"] != 0:
        return save_result

    return _result(0, "success", "workflow renamed successfully")


def find_workflows(query):
    workflows, error = _require_loaded_workflows(load_workflows())
    if error:
        return error

    query = query.lower()
    matches = {}

    for name, workflow in workflows.items():
        searchable_text = " ".join(
            [
                name,
                workflow.get("description", ""),
                " ".join(workflow.get("commands", [])),
            ]
        ).lower()
        if query in searchable_text:
            matches[name] = workflow

    return _result(0, "success", "workflow search completed", matches)


def export_workflows(destination):
    workflows, error = _require_loaded_workflows(load_workflows())
    if error:
        return error

    destination = Path(destination)
    try:
        _write_json_file(destination, workflows)
    except OSError as error:
        return _result(1, "error", f"could not export workflows: {error}")

    return _result(0, "success", f"workflows exported to {destination}")


def import_workflows(source, replace=False):
    source = Path(source)
    try:
        with source.open("r", encoding="utf-8") as file:
            imported = json.load(file)
    except FileNotFoundError:
        return _result(2, "warning", "import file not found")
    except json.JSONDecodeError:
        return _result(2, "warning", "import file is malformed")
    except (OSError, UnicodeDecodeError) as error:
        return _result(1, "error", f"could not import workflows: {error}")

    if not isinstance(imported, dict):
        return _result(2, "warning", "import file must contain a JSON object")

    current_workflows, error = _require_loaded_workflows(load_workflows())
    if error:
        return error

    workflows = {} if replace else current_workflows
    imported_count = 0
    skipped_count = 0

    for name, workflow in imported.items():
        clean_name, name_error = _validate_workflow_name(name)
        if name_error:
            skipped_count += 1
            continue
        if not isinstance(workflow, dict):
            skipped_count += 1
            continue
        if not replace and clean_name in workflows:
            skipped_count += 1
            continue

        normalized_workflow = _normalize_workflow(clean_name, workflow)
        if normalized_workflow is None:
            skipped_count += 1
            continue

        workflows[clean_name] = normalized_workflow
        imported_count += 1

    save_result = save_workflows(workflows)
    if save_result["code"] != 0:
        return save_result

    message = f"imported {imported_count} workflow"
    if imported_count != 1:
        message += "s"
    if skipped_count:
        message += f", skipped {skipped_count}"

    return _result(0, "success", message)
