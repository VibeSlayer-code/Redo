from pathlib import Path

from modules import storage


PROJECT_DIR_NAME = ".redo"
WORKFLOW_FILE_NAME = "workflows.json"
SOURCE_PROJECT = "project"
SOURCE_GLOBAL = "global"


def _result(code, status, message, data=None):
    result = {"code": code, "status": status, "message": message}
    if data is not None:
        result["data"] = data
    return result


def project_workflow_path(start=None, prefer_existing=True):
    start_path = Path.cwd() if start is None else Path(start)
    if start_path.is_file():
        start_path = start_path.parent

    if prefer_existing:
        existing = find_project_workflow_file(start_path)
        if existing is not None:
            return existing

    return start_path / PROJECT_DIR_NAME / WORKFLOW_FILE_NAME


def find_project_workflow_file(start=None):
    start_path = Path.cwd() if start is None else Path(start)
    if start_path.is_file():
        start_path = start_path.parent

    try:
        start_path = start_path.resolve()
    except OSError:
        start_path = start_path.absolute()

    for directory in (start_path, *start_path.parents):
        candidate = directory / PROJECT_DIR_NAME / WORKFLOW_FILE_NAME
        if candidate.exists():
            return candidate

    return None


def initialize_project_file(start=None):
    path = project_workflow_path(start, prefer_existing=False)
    result = storage.initialize_file_at(path)
    if result["code"] == 0:
        return {**result, "message": f"project workflow file initialized at {path}", "data": {"path": path}}
    if result["code"] == 2:
        return {**result, "message": f"project workflow file already exists at {path}", "data": {"path": path}}
    return {**result, "data": {"path": path}}


def load_project_workflows(start=None):
    path = find_project_workflow_file(start)
    if path is None:
        return _result(0, "success", "project workflow file not found", {},)

    result = storage.load_workflows_from(path, initialize_missing=False)
    if result["code"] != 0:
        return result

    return {**result, "data": result.get("data", {}), "path": path}


def save_project_workflows(workflows, start=None):
    path = project_workflow_path(start)
    return storage.save_workflows_to(path, workflows)


def load_global_workflows():
    return storage.load_workflows()


def load_visible_workflows(include_project=True, include_global=True, start=None):
    workflows = {}
    sources = {}

    if include_global:
        global_result = load_global_workflows()
        if global_result["code"] != 0:
            return global_result
        for name, workflow in global_result.get("data", {}).items():
            workflows[name] = workflow
            sources[name] = SOURCE_GLOBAL

    if include_project:
        project_result = load_project_workflows(start)
        if project_result["code"] != 0:
            return project_result
        for name, workflow in project_result.get("data", {}).items():
            workflows[name] = workflow
            sources[name] = SOURCE_PROJECT

    return _result(
        0,
        "success",
        "workflows loaded successfully",
        {"workflows": workflows, "sources": sources},
    )


def get_visible_workflow(name, start=None):
    name = str(name).strip()
    result = load_visible_workflows(start=start)
    if result["code"] != 0:
        return result

    workflows = result["data"]["workflows"]
    workflow = workflows.get(name)
    if workflow is None:
        return _result(2, "warning", "workflow not found", None)

    return _result(
        0,
        "success",
        "workflow found",
        {"workflow": workflow, "source": result["data"]["sources"].get(name, SOURCE_GLOBAL)},
    )


def delete_visible_workflow(name, start=None):
    found = get_visible_workflow(name, start=start)
    if found["code"] != 0:
        return found

    source = found["data"]["source"]
    if source == SOURCE_PROJECT:
        project_result = load_project_workflows(start)
        if project_result["code"] != 0:
            return project_result
        workflows = project_result.get("data", {})
        workflows.pop(str(name).strip(), None)
        save_result = storage.save_workflows_to(project_result["path"], workflows)
    else:
        save_result = storage.delete_workflow(name)

    if save_result["code"] != 0:
        return save_result

    return _result(0, "success", f"{source} workflow deleted successfully")


def increment_visible_runs(name, source, start=None):
    if source != SOURCE_PROJECT:
        return storage.increment_runs(name)

    project_result = load_project_workflows(start)
    if project_result["code"] != 0:
        return project_result

    workflows = project_result.get("data", {})
    name = str(name).strip()
    if name not in workflows:
        return _result(2, "warning", "workflow not found")

    try:
        workflows[name]["runs"] = int(workflows[name].get("runs", 0)) + 1
    except (TypeError, ValueError):
        workflows[name]["runs"] = 1

    save_result = storage.save_workflows_to(project_result["path"], workflows)
    if save_result["code"] != 0:
        return save_result

    return _result(0, "success", "workflow run count updated")
