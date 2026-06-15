# Redo

A CLI tool for saving repeated terminal workflows and running them again with one command.

<p align="center">
  <img src="https://images.guns.lol/deb9f1be54e955717bb3d9ed7d12fb5af82048b4/CLEHWv.png" alt="Redo banner" width="100%" />
</p>

<p align="center">
  <b>Stop retyping commands. Save workflows once, run them anytime.</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/redo-cli/">
    <img src="https://img.shields.io/pypi/v/redo-cli?style=for-the-badge&label=PyPI" alt="PyPI version">
  </a>
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/CLI-Workflow%20Automation-6D5DFB?style=for-the-badge" alt="CLI Workflow Automation">
  <img src="https://img.shields.io/badge/Status-Active-22C55E?style=for-the-badge" alt="Active">
</p>

<p align="center">
  <a href="#quick-start"><b>Quick Start</b></a>
  ·
  <a href="#how-it-works"><b>How It Works</b></a>
  ·
  <a href="#commands"><b>Commands</b></a>
  ·
  <a href="#placeholders"><b>Placeholders</b></a>
  ·
  <a href="#local-development"><b>Local Development</b></a>
</p>

---

## What is Redo?

Redo is a command-line tool that turns repeated terminal command chains into reusable workflows.

Instead of typing the same commands again and again:

```bash
git add .
git commit -m "fixed bug"
git push
```

Save them once:

```bash
redo new ship
```

Run them anytime:

```bash
redo run ship
```

Think of Redo as **bookmarks for terminal workflows**.

---

## Quick Start

Install Redo from PyPI:

```bash
pip install redo-cli
```

Check the available commands:

```bash
redo --help
```

Create a workflow:

```bash
redo new ship
```

Enter commands one by one:

```txt
Description: Commit and push code
Command: git add .
Command: git commit -m "{message}"
Command: git push
Command: :done
```

Run it later:

```bash
redo run ship
```

Preview it without running anything:

```bash
redo run ship --dry
```

---

## Getting Help

Use Redo’s built-in help whenever you forget a command:

```bash
redo --help
```

Show help for a specific command:

```bash
redo new --help
redo run --help
redo import --help
```

Running `redo` with no command shows the Redo banner.

Running this shows version, storage path, and credit:

```bash
redo --info
```

---

## Demo Flow

<p align="center">
  <img src="https://images.guns.lol/deb9f1be54e955717bb3d9ed7d12fb5af82048b4/CLTfIJ.png" alt="Redo demo running workflow" width="85%" />
</p>

A typical Redo session looks like this:

```bash
redo new ship
redo list
redo show ship
redo run ship --dry
redo run ship
redo stats
```

---

## Why It Matters

Developers repeat command chains constantly.

<table>
  <tr>
    <td><b>Project setup</b></td>
    <td><code>npm install</code>, copy env files, start dev servers</td>
  </tr>
  <tr>
    <td><b>Git workflows</b></td>
    <td><code>git add</code>, <code>git commit</code>, <code>git push</code></td>
  </tr>
  <tr>
    <td><b>Build flows</b></td>
    <td>run tests, build apps, deploy projects</td>
  </tr>
  <tr>
    <td><b>Cleanup flows</b></td>
    <td>remove build folders, reinstall dependencies, reset local state</td>
  </tr>
</table>

Redo removes the small friction that adds up over time.

---

## Features

| Feature            | What it does                                       |
| ------------------ | -------------------------------------------------- |
| Named workflows    | Save repeated command chains as reusable workflows |
| One-command replay | Run saved workflows with `redo run <name>`         |
| Smart placeholders | Use values like `{message}` or `{project_name}`    |
| Dry run mode       | Preview commands before executing them             |
| Safety checks      | Detect risky commands before they surprise you     |
| Focused errors     | Stop on failure and show the command that broke    |
| Usage stats        | Track run counts and time-saved estimates          |
| Import/export      | Back up and move workflows between machines        |
| Doctor/autofix     | Check and repair workflow storage issues           |

---

## Commands

Every command supports command-specific help:

```bash
redo <command> --help
```

### Core commands

```bash
redo init
redo new <name>
redo list
redo show <name>
redo run <name>
redo run <name> --dry
redo delete <name>
redo stats
```

### Utility commands

```bash
redo search <query>
redo copy <source> <target>
redo rename <old-name> <new-name>
redo path
redo export workflows-backup.json
redo import workflows-backup.json
redo import workflows-backup.json --replace
redo doctor
redo autofix
redo guide
redo clearhistory
```

---

## Example Workflow

Create a workflow:

```bash
redo new ship
```

Enter:

```txt
Description: Commit and push code
Command: git add .
Command: git commit -m "{message}"
Command: git push
Command: :done
```

Redo stores it like this:

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

Run it:

```bash
redo run ship
```

Redo asks for the placeholder value:

```txt
message: fixed clumsy ui
```

Then it runs:

```bash
git add .
git commit -m "fixed clumsy ui"
git push
```

---

## Placeholders

Use placeholders when part of a command changes each run.

```bash
git commit -m "{message}"
npm create vite@latest {project_name}
cd {project_name}
```

Redo asks once for each unique placeholder, then replaces every occurrence across the workflow.

Valid placeholder names:

```txt
{message}
{project_name}
{ticket_123}
```

Invalid placeholder names:

```txt
{123ticket}
{project-name}
{}
```

Placeholder values are quoted before execution so user input is treated as one literal value instead of shell syntax.

---

## Safety

Redo detects risky commands before running them.

Examples:

```bash
rm -rf
del /s
format
sudo
git reset --hard
```

If a risky command is found, Redo asks for confirmation before continuing.

Use dry-run mode whenever you want to inspect a workflow first:

```bash
redo run cleanup --dry
```

---

## Storage

Redo stores workflow data in:

```txt
%APPDATA%/Redo/workflows.json
```

If `APPDATA` is unavailable, Redo falls back to:

```txt
~/.redo/workflows.json
```

Print the exact storage path:

```bash
redo path
```

Override the storage directory:

```bash
REDO_DATA_DIR=<path>
```

Initialize storage manually:

```bash
redo init
```

Check storage health:

```bash
redo doctor
```

Repair common storage issues:

```bash
redo autofix
```

`redo autofix` can fix missing files, blank files, malformed JSON, and workflow entries with missing fields. If JSON is malformed, Redo saves a non-overwriting `workflows.broken.json` backup before resetting the main file.

---

## Local Development

Requirements:

```txt
Python 3.11+
```

Clone the repository:

```bash
git clone https://github.com/VibeSlayer-code/Redo.git
cd Redo
```

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
pip install -e .
```

Run locally:

```bash
python main.py --help
redo --help
redo --info
```

Run tests:

```bash
pytest
```

---

## How It Works

Redo is split into small modules instead of one large script.

```txt
storage.py       workflow JSON storage
placeholders.py  placeholder detection and replacement
runner.py        command execution and dry runs
ui.py            terminal output and tables
main.py          CLI commands
```

The workflow lifecycle:

```txt
load workflow
process placeholders
preview or run commands
stop on failure
update run count
```

This keeps the codebase simple while still supporting useful CLI features like dry runs, safety checks, repair tools, and stats.

---

## Git Push Tip

If Git says the current branch has no upstream branch, run the command Git suggests once:

```bash
git push --set-upstream origin master
```

After that, workflows containing `git push` can push normally.

---

## Roadmap

* Project-local workflow files
* Shell completion
* Workflow tags
* Workflow templates
* Shared workflows for repositories
* More detailed time-saved analytics
* Better safety rules for destructive commands

---

## License

Source-available, all rights reserved.

You may view the source code, but you may not copy, modify, distribute, or use it without permission.
