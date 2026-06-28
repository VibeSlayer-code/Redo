import re
import shutil
import socket
import subprocess
from pathlib import Path


TOOLS = ("git", "npm", "node", "python", "pip", "pytest", "cargo")
DEV_PORTS = (5173, 3000, 8000, 8080)
DEV_SERVER_PATTERNS = (
    "npm run dev",
    "vite",
    "next dev",
    "python -m http.server",
    "uvicorn",
    "fastapi",
)
RISKY_PATTERNS = ("git commit", "git push", "deploy", "release", "ship")


def _result(code, status, message, data=None):
    result = {"code": code, "status": status, "message": message}
    if data is not None:
        result["data"] = data
    return result


def _joined(commands):
    return "\n".join(str(command) for command in commands).lower()


def _tool_appears(tool, text):
    if tool == "python":
        return bool(re.search(r"\bpython(?:3)?\b", text))
    return bool(re.search(rf"\b{re.escape(tool)}\b", text))


def _required_tools(text):
    required = set()
    for tool in TOOLS:
        if _tool_appears(tool, text):
            required.add(tool)
    if "npm" in required:
        required.add("node")
    return sorted(required)


def _has_python_project_file(root):
    return any((root / filename).exists() for filename in ("requirements.txt", "pyproject.toml"))


def _is_port_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            return True
    except OSError:
        return False


def _git_tree_is_dirty(root):
    if not (root / ".git").exists():
        return False

    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False

    return completed.returncode == 0 and bool(completed.stdout.strip())


def run_preflight(name, commands, root=None):
    root = Path.cwd() if root is None else Path(root)
    text = _joined(commands)
    passed = []
    warnings = []
    errors = []
    fixes = []

    for tool in _required_tools(text):
        if shutil.which(tool):
            passed.append(f"{tool} found")
        else:
            errors.append(f"{tool} not found")
            fixes.append(f"install {tool}")

    if "npm" in text or "node" in text or "vite" in text or "next dev" in text:
        if (root / "package.json").exists():
            passed.append("package.json found")
        else:
            errors.append("package.json missing")
        if not (root / "node_modules").exists():
            warnings.append("node_modules missing")
            fixes.append("npm install")

    if any(token in text for token in ("python", "pip", "pytest", "uvicorn", "fastapi")):
        if _has_python_project_file(root):
            passed.append("Python project file found")
        else:
            errors.append("requirements.txt or pyproject.toml missing")
        if not (root / ".venv").exists():
            warnings.append(".venv missing")
            fixes.append("python -m venv .venv")

    if "cargo" in text:
        if (root / "Cargo.toml").exists():
            passed.append("Cargo.toml found")
        else:
            errors.append("Cargo.toml missing")

    if (root / ".env.example").exists() and not (root / ".env").exists():
        warnings.append(".env missing but .env.example exists")
        fixes.append("copy .env.example .env")

    if any(pattern in text for pattern in RISKY_PATTERNS) and _git_tree_is_dirty(root):
        warnings.append("Git working tree is dirty before a risky Git/deploy command")
        fixes.append("review git status")

    if any(pattern in text for pattern in DEV_SERVER_PATTERNS):
        for port in DEV_PORTS:
            if _is_port_open(port):
                warnings.append(f"port {port} appears to be in use")

    unique_fixes = []
    for fix in fixes:
        if fix not in unique_fixes:
            unique_fixes.append(fix)

    code = 1 if errors else 2 if warnings else 0
    status = "error" if errors else "warning" if warnings else "success"
    message = "preflight found errors" if errors else "preflight found warnings" if warnings else "preflight passed"
    return _result(
        code,
        status,
        message,
        {
            "name": name,
            "passed": passed,
            "warnings": warnings,
            "errors": errors,
            "fixes": unique_fixes,
        },
    )
