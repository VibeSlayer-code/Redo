from copy import deepcopy


BUILTIN_TEMPLATES = {
    "ship": {
        "description": "Commit and push code",
        "commands": ["git add .", 'git commit -m "{message}"', "git push"],
    },
    "python-test": {
        "description": "Run Python tests",
        "commands": ["pytest"],
    },
    "node-dev": {
        "description": "Install dependencies and start a Node dev server",
        "commands": ["npm install", "npm run dev"],
    },
    "clean-python": {
        "description": "Remove common Python cache folders",
        "commands": [
            "python -c \"import pathlib, shutil; [shutil.rmtree(path, ignore_errors=True) for path in pathlib.Path('.').rglob('__pycache__')]\"",
            "python -c \"import pathlib; [path.unlink(missing_ok=True) for path in pathlib.Path('.').rglob('*.pyc')]\"",
        ],
    },
    "build": {
        "description": "Run tests and build the package",
        "commands": ["pytest", "python -m build"],
    },
}


def list_templates():
    return deepcopy(BUILTIN_TEMPLATES)


def get_template(name):
    template = BUILTIN_TEMPLATES.get(str(name).strip())
    if template is None:
        return None
    return deepcopy(template)
