import json
from copy import deepcopy
from pathlib import Path


DATA_DIR = Path("C:/redo/files")
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


def initialize_file():
    if DATA_FILE.exists():
        if DATA_FILE.read_text(encoding="utf-8").strip():
            return _result(2, "warning", "workflow file already exists")

    try:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text("{}", encoding="utf-8")
        return _result(0, "success", "workflow file initialized")
    except OSError as error:
        return _result(1, "error", f"could not initialize workflow file: {error}")


def _broken_backup_file():
    return DATA_FILE.with_name(f"{DATA_FILE.stem}.broken.json")


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
        fixed_workflow = _normalize_workflow(name, workflow)
        if fixed_workflow is not None:
            normalized[name] = fixed_workflow

    return normalized


def autofix_storage():
    fixes = []

    try:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        return _result(1, "error", f"could not create Redo data directory: {error}")

    if not DATA_FILE.exists():
        DATA_FILE.write_text("{}", encoding="utf-8")
        fixes.append("created workflow file")
        return _result(0, "success", "autofix completed", {"fixes": fixes})

    raw_text = DATA_FILE.read_text(encoding="utf-8")
    if not raw_text.strip():
        DATA_FILE.write_text("{}", encoding="utf-8")
        fixes.append("reset blank workflow file")
        return _result(0, "success", "autofix completed", {"fixes": fixes})

    try:
        workflows = json.loads(raw_text)
    except json.JSONDecodeError:
        backup_file = _broken_backup_file()
        backup_file.write_text(raw_text, encoding="utf-8")
        DATA_FILE.write_text("{}", encoding="utf-8")
        fixes.append("backed up malformed workflow file")
        fixes.append("reset workflow file")
        return _result(0, "success", "autofix completed", {"fixes": fixes})

    normalized = _normalize_workflows(workflows)
    if normalized != workflows:
        save_result = save_workflows(normalized)
        if save_result["code"] != 0:
            return save_result
        fixes.append("normalized workflow entries")

    if not fixes:
        fixes.append("no fixes needed")

    return _result(0, "success", "autofix completed", {"fixes": fixes})


def load_workflows():
    if not DATA_FILE.exists() or not DATA_FILE.read_text(encoding="utf-8").strip():
        init_result = initialize_file()
        if init_result["code"] == 1:
            return {**init_result, "data": {}}

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError:
        return _result(2, "warning", "workflow file is malformed", {})
    except OSError as error:
        return _result(1, "error", f"could not load workflows: {error}", {})

    if not isinstance(data, dict):
        return _result(2, "warning", "workflow file must contain a JSON object", {})

    return _result(0, "success", "workflows loaded successfully", data)


def save_workflows(workflows):
    if not isinstance(workflows, dict):
        return _result(1, "error", "workflows must be a dictionary")

    try:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with DATA_FILE.open("w", encoding="utf-8") as file:
            json.dump(workflows, file, indent=2)
            file.write("\n")
    except OSError as error:
        return _result(1, "error", f"could not save workflows: {error}")

    return _result(0, "success", "workflows saved successfully")


def add_workflow(name, description, commands):
    result = load_workflows()
    if result["code"] == 1:
        return result

    workflows = result["data"]
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
    result = load_workflows()
    if result["code"] == 1:
        return result

    workflow = result["data"].get(name)
    if workflow is None:
        return _result(2, "warning", "workflow not found", None)

    return _result(0, "success", "workflow found", workflow)


def delete_workflow(name):
    result = load_workflows()
    if result["code"] == 1:
        return result

    workflows = result["data"]
    if name not in workflows:
        return _result(2, "warning", "workflow not found")

    del workflows[name]
    save_result = save_workflows(workflows)
    if save_result["code"] != 0:
        return save_result

    return _result(0, "success", "workflow deleted successfully")


def increment_runs(name):
    result = load_workflows()
    if result["code"] == 1:
        return result

    workflows = result["data"]
    if name not in workflows:
        return _result(2, "warning", "workflow not found")

    workflows[name]["runs"] = int(workflows[name].get("runs", 0)) + 1
    save_result = save_workflows(workflows)
    if save_result["code"] != 0:
        return save_result

    return _result(0, "success", "workflow run count updated")


def copy_workflow(source_name, target_name):
    result = load_workflows()
    if result["code"] == 1:
        return result

    workflows = result["data"]
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
    result = load_workflows()
    if result["code"] == 1:
        return result

    workflows = result["data"]
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
    result = load_workflows()
    if result["code"] == 1:
        return result

    query = query.lower()
    matches = {}

    for name, workflow in result["data"].items():
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
    result = load_workflows()
    if result["code"] == 1:
        return result

    destination = Path(destination)
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as file:
            json.dump(result["data"], file, indent=2)
            file.write("\n")
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
    except OSError as error:
        return _result(1, "error", f"could not import workflows: {error}")

    if not isinstance(imported, dict):
        return _result(2, "warning", "import file must contain a JSON object")

    current_result = load_workflows()
    if current_result["code"] == 1:
        return current_result

    workflows = {} if replace else current_result["data"]
    imported_count = 0
    skipped_count = 0

    for name, workflow in imported.items():
        if not isinstance(workflow, dict):
            skipped_count += 1
            continue
        if not replace and name in workflows:
            skipped_count += 1
            continue

        workflows[name] = {
            "description": workflow.get("description", ""),
            "commands": workflow.get("commands", []),
            "runs": int(workflow.get("runs", 0)),
        }
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

