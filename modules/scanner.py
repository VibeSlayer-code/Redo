import json
from pathlib import Path

from modules import project, storage


def _result(code, status, message, data=None):
    result = {"code": code, "status": status, "message": message}
    if data is not None:
        result["data"] = data
    return result


def _workflow(description, commands):
    return {
        "description": description,
        "commands": commands,
        "runs": 0,
    }


def _read_package_json(root):
    package_file = root / "package.json"
    try:
        with package_file.open("r", encoding="utf-8-sig") as file:
            package = json.load(file)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}

    return package if isinstance(package, dict) else {}


def _node_workflows(root):
    package = _read_package_json(root)
    scripts = package.get("scripts", {})
    if not isinstance(scripts, dict):
        scripts = {}

    workflows = {
        "install": _workflow("Install Node dependencies.", ["npm install"]),
        "clean": _workflow(
            "Remove common Node build and dependency folders after confirmation.",
            [
                "python -c \"import pathlib, shutil; "
                "targets=('dist','build','.next','cache','node_modules'); "
                "existing=[t for t in targets if pathlib.Path(t).exists()]; "
                "print('Targets: '+(', '.join(existing) if existing else 'none')); "
                "answer=input('Remove these folders? (y/N) '); "
                "[shutil.rmtree(pathlib.Path(t), ignore_errors=True) for t in existing] if answer.lower() in ('y','yes') else None\""
            ],
        ),
    }

    if "dev" in scripts:
        workflows["dev"] = _workflow("Start the Node development server.", ["npm run dev"])
    if "build" in scripts:
        workflows["build"] = _workflow("Build the Node project.", ["npm run build"])
    if "test" in scripts:
        workflows["test"] = _workflow("Run Node tests.", ["npm test"])

    return workflows


def _python_workflows(root):
    workflows = {
        "test": _workflow("Run Python tests.", ["pytest"]),
        "clean": _workflow(
            "Remove Python cache directories.",
            [
                "python -c \"import pathlib, shutil; "
                "[shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; "
                "shutil.rmtree('.pytest_cache', ignore_errors=True)\""
            ],
        ),
    }
    if (root / "requirements.txt").exists():
        workflows["install"] = _workflow("Install Python dependencies.", ["pip install -r requirements.txt"])
    return workflows


def _rust_workflows(root):
    return {
        "build": _workflow("Build the Rust project.", ["cargo build"]),
        "test": _workflow("Run Rust tests.", ["cargo test"]),
        "run": _workflow("Run the Rust project.", ["cargo run"]),
        "clean": _workflow("Clean Rust build artifacts.", ["cargo clean"]),
    }


def detect_project(root=None):
    root = Path.cwd() if root is None else Path(root)

    if (root / "package.json").exists():
        return _result(
            0,
            "success",
            "Detected Node project.",
            {"type": "Node", "workflows": _node_workflows(root), "root": root},
        )

    if any((root / filename).exists() for filename in ("requirements.txt", "pyproject.toml", "setup.py")):
        return _result(
            0,
            "success",
            "Detected Python project.",
            {"type": "Python", "workflows": _python_workflows(root), "root": root},
        )

    if (root / "Cargo.toml").exists():
        return _result(
            0,
            "success",
            "Detected Rust project.",
            {"type": "Rust", "workflows": _rust_workflows(root), "root": root},
        )

    return _result(2, "warning", "No supported project type detected.", {"type": None, "workflows": {}, "root": root})


def write_project_workflows(suggested, overwrite=False, root=None):
    root = Path.cwd() if root is None else Path(root)
    path = project.project_workflow_path(root)
    load_result = storage.load_workflows_from(path, initialize_missing=False)
    if load_result["code"] != 0:
        return load_result

    workflows = load_result.get("data", {})
    written = []
    skipped = []
    overwritten = []

    for name, workflow in suggested.items():
        name_result = storage.validate_workflow_name(name)
        if name_result["code"] != 0:
            skipped.append(name)
            continue
        if name in workflows and not overwrite:
            skipped.append(name)
            continue
        if name in workflows:
            overwritten.append(name)
        else:
            written.append(name)
        workflows[name] = workflow

    save_result = storage.save_workflows_to(path, workflows)
    if save_result["code"] != 0:
        return save_result

    return _result(
        0,
        "success",
        "project workflows updated",
        {"path": path, "written": written, "skipped": skipped, "overwritten": overwritten},
    )
