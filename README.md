# Redo

**Bookmarks for terminal workflows.**

Redo saves command chains you type again and again, then runs them later with one short command. It is built for developers, students, and hackathon builders who want repeatable setup, test, build, clean, and ship workflows without memorizing long README sections.

![Redo banner](https://images.guns.lol/deb9f1be54e955717bb3d9ed7d12fb5af82048b4/CLEHWv.png)

## 3 Major QoL Improvements

1. **Project-local workflows** - store workflows in `.redo/workflows.json` so each project can ship setup, dev, build, test, and deploy commands.
2. **Automatic workflow generation** - `redo setup` scans the project and generates useful workflows automatically.
3. **Preflight checks** - `redo preflight <name>` and `redo run <name> --preflight` catch missing tools, missing files, missing dependencies, dirty Git state, and busy ports before commands fail.

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
| Project workflows | Keep workflows inside `.redo/workflows.json` for each repository. |
| Setup scanner | Generate install, dev, build, test, run, and clean workflows from common project files. |
| Preflight checks | Catch missing tools, files, env setup, dependencies, and busy dev ports. |
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

Generate project workflows automatically:

```bash
redo setup --dry
redo setup --yes
redo list --project
```

Check before running:

```bash
redo preflight dev
redo run dev --preflight
```

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
| `redo init --project` | Create `.redo/workflows.json` in the current project. |
| `redo setup` | Scan the current project and suggest project-local workflows. |
| `redo setup --dry` | Preview generated workflows without writing files. |
| `redo setup --yes` | Generate project workflows without an extra confirmation prompt. |
| `redo new <name>` | Create a workflow interactively. |
| `redo use <template> <name>` | Create a workflow from a template. |
| `redo run <name>` | Run a saved workflow. |
| `redo run <name> --dry` | Preview commands without running them. |
| `redo run <name> --preflight` | Check the project before running the workflow. |
| `redo run <name> --show-output` | Show captured output after successful commands. |
| `redo edit <name>` | Edit a saved workflow. |
| `redo list` | List workflows. |
| `redo list --project` | List only project-local workflows. |
| `redo list --global` | List only global workflows. |
| `redo show <name>` | Show workflow details. |
| `redo preflight <name>` | Run checks without executing the workflow. |
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
redo path --project
redo folder
redo clearhistory
```

## Project-Local Workflows

Create project storage:

```bash
redo init --project
```

Redo writes:

```txt
.redo/workflows.json
```

When you run, list, show, lint, or inspect workflows, Redo checks project workflows first and global workflows second. If both locations contain `dev`, the project-local `dev` workflow wins inside that project.

## Automatic Setup

`redo setup` detects common project types:

| Project | Detection | Suggested workflows |
| --- | --- | --- |
| Node | `package.json` | `install`, script-backed `dev`, `build`, `test`, plus confirmed `clean` |
| Python | `requirements.txt`, `pyproject.toml`, or `setup.py` | `install`, `test`, `clean` |
| Rust | `Cargo.toml` | `build`, `test`, `run`, `clean` |

Generated workflows are project-local and include descriptions. Existing project workflows are not overwritten unless you confirm.

## Preflight Checks

Run checks without executing commands:

```bash
redo preflight dev
```

Or check first, then run:

```bash
redo run dev --preflight
```

Preflight checks for tools such as `git`, `npm`, `node`, `python`, `pip`, `pytest`, and `cargo`; project files such as `package.json`, `requirements.txt`, `pyproject.toml`, and `Cargo.toml`; missing `node_modules`, missing `.venv`, `.env.example` without `.env`, dirty Git state for risky deploy-style commands, and common busy dev ports.

## Frictionless Mission Fit

The v1.2.0 QoL work maps directly to Frictionless:

1. **Project-local workflows** reduce setup drift because each repository can carry its own repeatable commands.
2. **Automatic workflow generation** removes the blank-page problem for new users by turning existing project files into useful Redo workflows.
3. **Preflight checks** catch common failure points before a workflow starts, making `setup`, `dev`, `build`, `test`, and `ship` feel predictable.

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

Project workflows live in `.redo/workflows.json` and can be located with:

```bash
redo path --project
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
