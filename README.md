# Redo

**Bookmarks for terminal workflows.**

Redo saves command chains you type again and again, then runs them later with one short command. It is built for developers, students, and hackathon builders who want repeatable setup, test, build, clean, and ship workflows without memorizing long README sections.

![Redo banner](https://images.guns.lol/deb9f1be54e955717bb3d9ed7d12fb5af82048b4/CLEHWv.png)

## Why Redo Exists

Every project has commands that people keep retyping:

```bash
git add .
git commit -m "fixed ui"
git push
```

```bash
npm install
npm run dev
```

```bash
pytest
python -m build
```

Redo turns those repeated chains into named workflows:

```bash
redo run ship
redo run dev
redo run build
```

## Highlights

| Feature | Why it matters |
| --- | --- |
| Named workflows | Save command chains once and run them anytime. |
| Placeholders | Use values like `{message}` or `{project_name}` at run time. |
| Rich run UI | See clean progress, status, failures, and optional command output. |
| Dry runs | Preview exactly what will run before executing anything. |
| Edit command | Fix saved workflows without deleting and recreating them. |
| Templates | Start from useful built-in developer workflow templates. |
| Linting | Catch comma-separated command mistakes, risky commands, and typos. |
| Update checks | Redo can tell users when a newer release is available and install it. |
| Doctor/autofix | Diagnose and repair common storage problems. |
| Import/export/backup | Move workflows between machines or keep backups. |

## Install

```bash
pip install redo-cli
```

Upgrade:

```bash
pip install --upgrade redo-cli
```

Or let Redo check and upgrade itself:

```bash
redo update
```

Verify:

```bash
redo --info
```

## Quick Start

Create a workflow:

```bash
redo new ship
```

Enter one command per prompt:

```txt
Description: Commit and push code
Command: git add .
Command: git commit -m "{message}"
Command: git push
Command: :done
```

Run it:

```bash
redo run ship
```

Redo asks for the placeholder value:

```txt
message: added dark mode
```

Then Redo runs:

```bash
git add .
git commit -m "added dark mode"
git push
```

Preview first:

```bash
redo run ship --dry
```

Show successful command output:

```bash
redo run ship --show-output
```

## Templates

Templates make Redo useful immediately:

```bash
redo templates
redo use ship ship
redo use python-test test
redo use node-dev dev
```

The `ship` template creates:

```bash
git add .
git commit -m "{message}"
git push
```

## Core Commands

| Command | Purpose |
| --- | --- |
| `redo new <name>` | Create a workflow interactively. |
| `redo use <template> <name>` | Create a workflow from a template. |
| `redo run <name>` | Run a saved workflow. |
| `redo run <name> --dry` | Preview commands without running them. |
| `redo run <name> --show-output` | Show captured output after successful commands. |
| `redo edit <name>` | Edit a saved workflow. |
| `redo list` | List workflows. |
| `redo show <name>` | Show workflow details. |
| `redo search <query>` | Search names, descriptions, and commands. |
| `redo lint` | Find common workflow mistakes. |
| `redo stats` | Show usage and estimated time saved. |
| `redo update` | Check for a newer Redo release and install it. |
| `redo update --check-only` | Check for updates without installing. |

## Maintenance Commands

```bash
redo doctor
redo autofix
redo backup --dir backups
redo export workflows.json
redo import workflows.json
redo path
redo folder
redo clearhistory
```

## Placeholders

Use placeholders for values that change each run:

```bash
git commit -m "{message}"
npm create vite@latest {project_name}
cd {project_name}
```

Valid placeholder names use letters, numbers, and underscores, and cannot start with a number:

```txt
{message}
{project_name}
{ticket_123}
```

Redo asks once for each unique placeholder and reuses the value everywhere in the workflow.

## Safety

Redo warns before running risky commands such as:

```txt
rm -rf
del /s
format
sudo
git reset --hard
```

Use `--dry` before running a workflow for the first time.

## Storage

Redo stores workflows in:

```txt
%APPDATA%/Redo/workflows.json
```

You can print the exact path:

```bash
redo path
```

For testing or custom setups, override the storage directory:

```bash
REDO_DATA_DIR=<path>
```

## Contributing

Contributions are welcome. Good first improvements include:

- workflow templates for popular tools
- better lint rules
- clearer Windows/macOS/Linux shell support
- documentation improvements
- focused tests for edge cases

Read [docs.md](docs.md) before opening a PR. It explains the architecture, command flow, storage contract, testing approach, and contribution standards.

## Development

```bash
git clone https://github.com/VibeSlayer-code/Redo.git
cd Redo
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
pytest
```

Build:

```bash
python -m build
```

## Credit

Created by Vibeslayer-code.

## License

See [license.txt](license.txt).
