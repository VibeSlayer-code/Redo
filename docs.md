# Redo Contributor Guide

This document explains how Redo works and how to contribute without breaking the CLI experience.

Redo is a Python CLI for saving repeated terminal workflows and running them again with one command. The project should stay small, readable, and beginner-friendly.

## Project Layout

```txt
Redo/
  main.py                 Typer command definitions and CLI flow
  README.md               User-facing project page
  docs.md                 Contributor guide
  pyproject.toml          Packaging metadata and console script
  requirements.txt        Runtime dependencies for local installs
  license.txt             License terms
  assets/                 README images and demo media
  modules/
    storage.py            Workflow JSON and state storage
    placeholders.py       Placeholder parsing and replacement
    runner.py             Command execution, dry runs, status UI
    inspector.py          Workflow linting
    templates.py          Built-in workflow templates
    update_checker.py     PyPI update checks and caching
    ui.py                 Rich terminal UI helpers
  tests/                  Pytest suite
```

The code intentionally avoids a complex framework. Most behavior lives in small modules, and `main.py` connects those modules to Typer commands.

## Architecture

Redo has five main layers:

1. **CLI layer**
   `main.py` defines user commands such as `redo new`, `redo run`, `redo edit`, `redo lint`, and `redo update`.

2. **Storage layer**
   `modules/storage.py` owns workflow and state files. Workflow data is stored as JSON. State data stores small tool preferences such as first-run guide status and update-check cache.

3. **Placeholder layer**
   `modules/placeholders.py` detects placeholders like `{message}` and replaces them with user-provided values.

4. **Runner layer**
   `modules/runner.py` executes workflow commands, handles dry runs, detects dangerous commands, stops on failure, and reports command output.

5. **Presentation layer**
   `modules/ui.py` owns Rich output. New commands should prefer UI helpers over hand-built print blocks in `main.py`.

## Storage Contract

Workflows are stored in:

```txt
%APPDATA%/Redo/workflows.json
```

If `APPDATA` is unavailable, Redo falls back to:

```txt
~/.redo/workflows.json
```

Tests can redirect storage with:

```bash
REDO_DATA_DIR=<path>
```

A workflow looks like:

```json
{
  "ship": {
    "description": "Commit and push code",
    "commands": [
      "git add .",
      "git commit -m \"{message}\"",
      "git push"
    ],
    "runs": 0
  }
}
```

All storage functions should return dictionaries with this shape:

```python
{
    "code": 0,
    "status": "success",
    "message": "human readable message",
    "data": {}
}
```

Use these codes consistently:

| Code | Meaning |
| --- | --- |
| `0` | Success |
| `1` | Real error |
| `2` | Warning, not found, already exists, or user-correctable issue |

## Command Flow

`redo run <name>` follows this flow:

```txt
load workflow
process placeholders
preview commands if --dry
check for dangerous commands
run commands in order
stop if one fails
increment run count on success
```

`redo new <name>` should validate early. Do not ask users for description and commands if the workflow name is invalid or already exists.

`redo edit <name>` should preserve run counts and update only description/commands.

## Update Detection

`modules/update_checker.py` checks PyPI for the latest `redo-cli` version.

Rules:

- Update checks must never crash normal CLI commands.
- Auto-checks are cached for one day.
- Tests disable auto-checking with `REDO_DISABLE_UPDATE_CHECK=1`.
- `redo update` forces a fresh check and installs the latest package when a newer version exists.
- `redo update --check-only` forces a fresh check without installing.
- If automatic installation fails, show the manual upgrade command:

```bash
pip install --upgrade redo-cli
```

## Templates

Templates live in `modules/templates.py`.

Each template needs:

```python
{
    "description": "Short description",
    "commands": ["command one", "command two"]
}
```

Good templates are:

- common across many projects
- easy to understand
- safe by default
- useful immediately after install

Avoid templates that delete files unless they are extremely clear and covered by safety checks.

## Lint Rules

Workflow linting lives in `modules/inspector.py`.

Current lint checks include:

- empty workflows
- empty commands
- commands that look comma-separated
- dangerous commands
- placeholder typos such as `{messgae}`
- duplicate command chains

Lint should guide users, not shame them. Messages should explain what to fix in plain language.

## UI Guidelines

Redo uses Rich for terminal output. Keep UI:

- clean
- readable
- consistent
- useful for beginners
- not overly colorful

Use `modules/ui.py` for tables, panels, status messages, and reports.

Avoid adding large explanatory text inside normal command output. Put deeper explanations in README or this document.

## Testing

Run:

```bash
pytest
```

Tests should cover:

- storage behavior with `tmp_path`
- malformed JSON handling
- CLI command success and failure paths
- placeholder parsing/replacement
- runner dry-run and failure behavior
- update checker cache behavior
- lint and template behavior

Do not let tests write to the real user workflow file. Use `tmp_path`, `monkeypatch`, or `REDO_DATA_DIR`.

## Adding A New Command

Use this checklist:

1. Add tests first in `tests/test_cli.py` or a focused module test.
2. Put core logic in a module under `modules/`.
3. Add a small command wrapper in `main.py`.
4. Add UI helpers in `modules/ui.py` if output is more than one line.
5. Add the command name to `RESERVED_WORKFLOW_NAMES` in `storage.py`.
6. Update README if users need to know about it.
7. Update this file if contributors need to understand it.
8. Run the full test suite.

## Release Checklist

Before publishing a release:

1. Update `VERSION` in `main.py`.
2. Update `version` in `pyproject.toml`.
3. Run:

```bash
pytest
python -m build
```

4. Smoke test the CLI with a temporary data directory:

```bash
REDO_DATA_DIR=<temp-path> redo --help
REDO_DATA_DIR=<temp-path> redo templates
REDO_DATA_DIR=<temp-path> redo use ship ship
REDO_DATA_DIR=<temp-path> redo run ship --dry
```

5. Check that README and docs still match the command list.

## Pull Request Expectations

A good PR should:

- solve one clear problem
- include tests
- keep command output clean
- avoid unrelated refactors
- preserve existing workflows
- avoid writing to real user storage during tests
- explain user-facing behavior in the PR description

Small, focused PRs are easier to review and more likely to be merged.

## Maintainer Notes

Redo should feel polished, but not complicated. Prefer features that remove real terminal friction:

- editing instead of deleting and recreating
- templates instead of memorizing setup commands
- linting instead of silent confusion
- update notices instead of stale installs
- backups instead of fear

When deciding whether to add a feature, ask:

```txt
Will this help someone run repeated workflows faster, safer, or with less confusion?
```

If yes, it probably belongs in Redo. If not, keep it out.
