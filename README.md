# Redo

Redo is a CLI tool that saves repeated terminal workflows and runs them again with one command. It is built for developers who are tired of retyping the same setup, build, deploy, and cleanup commands.

Think of it as bookmarks for terminal workflows.

## Why Redo Exists

Developers repeat the same command chains constantly: starting projects, running test suites, cleaning folders, pushing code, building apps, and following long README setup steps.

Redo lets you define those workflows once, then replay them whenever you need them. It supports smart placeholders, previews, safety checks for dangerous commands, and simple usage stats.

## Installation

Install from PyPI:

```bash
pip install redo-cli
```

For local development, clone the project, create a virtual environment, and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

You can run Redo locally with either form:

```bash
python main.py --help
redo --help
redo --info
```

Running `redo` with no command shows the Redo ASCII banner. Running `redo --info` shows the banner, version, storage path, and credit.

Redo stores its workflow data in:

```txt
%APPDATA%/Redo/workflows.json on Windows, or ~/.redo/workflows.json when APPDATA is unavailable
```

Set `REDO_DATA_DIR` to override the storage directory. Run `redo path` to print the exact file Redo is using.

Run `redo init` to create the folder and file explicitly, or let Redo create them the first time it needs storage.

The first time you run `redo new`, Redo offers to show a quick guide. You can open that guide anytime with:

```bash
redo guide
```

## Usage

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

Redo shows a live status table while commands run. Successful command output stays quiet by default; if a command fails, Redo stops the workflow and shows a focused error panel with the captured output.

Preview it without executing commands:

```bash
redo run ship --dry
```

## Commands

```bash
redo init
redo new <name>
redo list
redo show <name>
redo run <name>
redo run <name> --dry
redo delete <name>
redo clearhistory
redo stats
```

Developer QoL commands:

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
```

`redo doctor` checks the workflow file, counts saved commands/placeholders, and flags risky commands before they surprise you later.

`redo autofix` repairs common storage problems: missing files, blank files, malformed JSON, and workflow entries with missing fields. If JSON is malformed, Redo saves a non-overwriting `workflows.broken.json` backup next to the main file before resetting it.

`redo clearhistory` clears every saved workflow from the file shown by `redo path`. Use `redo clearhistory --yes` to skip the confirmation prompt.

## Placeholders

Use placeholders when part of a command changes each run:

```bash
git commit -m "{message}"
npm create vite@latest {project_name}
cd {project_name}
```

Redo asks once for each unique placeholder, then replaces every occurrence across the workflow.

Valid placeholder names use letters, numbers, and underscores, and cannot start with a number:

```txt
{message}
{project_name}
{ticket_123}
```

Placeholder values are quoted before execution so prompt input is treated as one literal value instead of shell syntax. This prevents command separators, variable expansion, and globs from silently changing the command shape.

Workflow names cannot be blank or reuse Redo command names such as `run`, `new`, `delete`, or `stats`.

## Demo Workflow

```bash
redo new ship
redo list
redo show ship
redo run ship --dry
redo run ship
redo stats
```

Example workflow data:

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

## Safety

Redo detects risky commands before running them and asks for confirmation. Examples include:

```bash
rm -rf
del /s
format
sudo
git reset --hard
```

## Git Push Tip

If Git says the current branch has no upstream branch, run the command Git suggests once:

```bash
git push --set-upstream origin master
```

After that, a workflow containing `git push` can push normally.

## Roadmap

- Project-local and global workflow stores
- Tags and search
- Shell completion
- Workflow sharing through repository templates
- More detailed time-saved analytics
