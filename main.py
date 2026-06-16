import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.prompt import Confirm, Prompt

from modules import inspector, placeholders, runner, storage, templates, ui, update_checker


VERSION = "1.1.6"
CREDIT = "Vibeslayer-code"
COMMAND_CONTEXT = {"help_option_names": ["--help", "-h"]}

app = typer.Typer(
    help="Redo saves repeated terminal workflows and runs them again with one command.",
    no_args_is_help=False,
    context_settings={"help_option_names": []},
)


def _print_result(result):
    if result["code"] == 0:
        ui.print_success(result["message"])
    elif result["code"] == 2:
        ui.print_warning(result["message"])
    else:
        ui.print_error(result["message"])


def _exit_for_result(result):
    return 0 if result["code"] == 0 else 1


def _failure_exit_for_result(result):
    return 1 if result["code"] == 1 else 0


def _raise_for_result(result):
    raise typer.Exit(code=_exit_for_result(result))


def _offer_first_run_guide():
    if not storage.should_offer_first_run_guide():
        return

    if Confirm.ask("First time using Redo? See the quick guide first?", default=True):
        ui.show_guide()

    result = storage.mark_first_run_guide_seen()
    if result["code"] != 0:
        ui.print_warning(result["message"])


def _maybe_show_update_notice(command_name):
    if command_name in {None, "update"}:
        return

    result = update_checker.check_for_update(VERSION)
    if result["code"] == 2 and result.get("data", {}).get("update_available"):
        latest = result["data"].get("latest_version", "latest")
        ui.print_warning(
            f"Redo {latest} is available. You are using {VERSION}. "
            "Run: pip install --upgrade redo-cli"
        )


@app.callback(invoke_without_command=True)
def root(
    ctx: typer.Context,
    help: bool = typer.Option(False, "--help", "-h", help="Show Redo help menu."),
    info: bool = typer.Option(False, "--info", help="Show Redo version and credits."),
):
    """Bookmarks for terminal workflows."""
    if help:
        ui.show_help_menu(VERSION)
        raise typer.Exit(code=0)

    if info:
        ui.show_info(VERSION, CREDIT, storage_path=str(storage.DATA_FILE.resolve()), animated=True)
        raise typer.Exit(code=0)

    if ctx.invoked_subcommand is None:
        ui.show_banner()
        raise typer.Exit(code=0)

    _maybe_show_update_notice(ctx.invoked_subcommand)


@app.command("init", context_settings=COMMAND_CONTEXT)
def init():
    """Create Redo workflow storage if needed."""
    result = storage.initialize_file()
    _print_result(result)
    raise typer.Exit(code=_failure_exit_for_result(result))


@app.command("new", context_settings=COMMAND_CONTEXT)
def new_workflow(name: str = typer.Argument(..., help="Workflow name to create.")):
    """Create a reusable workflow."""
    name_result = storage.validate_workflow_name(name)
    if name_result["code"] != 0:
        _print_result(name_result)
        raise typer.Exit(code=1)

    storage_result = storage.load_workflows()
    if storage_result["code"] != 0:
        _print_result(storage_result)
        raise typer.Exit(code=1)
    if str(name).strip() in storage_result.get("data", {}):
        ui.print_warning("workflow already exists")
        raise typer.Exit(code=1)

    _offer_first_run_guide()
    description = Prompt.ask("Description")
    commands = []

    while True:
        command = Prompt.ask("Command")
        if command.strip() == ":done":
            break
        if command.strip():
            commands.append(command)

    if not commands:
        ui.print_warning("No commands entered. Workflow was not saved.")
        raise typer.Exit(code=1)

    result = storage.add_workflow(name, description, commands)
    _print_result(result)
    _raise_for_result(result)


@app.command("list", context_settings=COMMAND_CONTEXT)
def list_workflows():
    """List saved workflows."""
    result = storage.load_workflows()
    if result["code"] != 0:
        _print_result(result)
        raise typer.Exit(code=1)

    ui.show_workflows_table(result["data"])


@app.command("search", context_settings=COMMAND_CONTEXT)
def search_workflows(query: str = typer.Argument(..., help="Text to find in workflows.")):
    """Search workflow names, descriptions, and commands."""
    result = storage.find_workflows(query)
    if result["code"] != 0:
        _print_result(result)
        raise typer.Exit(code=1)

    ui.show_workflows_table(result["data"])


@app.command("templates", context_settings=COMMAND_CONTEXT)
def list_templates():
    """Show built-in workflow templates."""
    ui.show_templates_table(templates.list_templates())


@app.command("use", context_settings=COMMAND_CONTEXT)
def use_template(
    template_name: str = typer.Argument(..., help="Template to use."),
    name: str = typer.Argument(..., help="Workflow name to create."),
):
    """Create a workflow from a built-in template."""
    template = templates.get_template(template_name)
    if template is None:
        ui.print_warning("template not found")
        raise typer.Exit(code=1)

    result = storage.add_workflow(name, template["description"], template["commands"])
    _print_result(result)
    _raise_for_result(result)


@app.command("show", context_settings=COMMAND_CONTEXT)
def show_workflow(name: str = typer.Argument(..., help="Workflow name to inspect.")):
    """Show workflow details."""
    result = storage.get_workflow(name)
    if result["code"] != 0:
        _print_result(result)
        raise typer.Exit(code=1)

    ui.show_workflow_details(name, result["data"])


@app.command("edit", context_settings=COMMAND_CONTEXT)
def edit_workflow(
    name: str = typer.Argument(..., help="Workflow name to edit."),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Replacement description."),
    commands: Optional[list[str]] = typer.Option(
        None,
        "--command",
        "-c",
        help="Replacement command. Use multiple times for multiple commands.",
    ),
):
    """Edit a saved workflow without deleting it."""
    result = storage.get_workflow(name)
    if result["code"] != 0:
        _print_result(result)
        raise typer.Exit(code=1)

    workflow = result["data"]
    new_description = description
    new_commands = commands

    if new_description is None and not new_commands:
        ui.show_workflow_details(name, workflow)
        new_description = Prompt.ask("Description", default=workflow.get("description", ""))
        ui.print_warning("Enter replacement commands one per line. Type :done to finish, or :done immediately to keep current commands.")
        collected_commands = []

        while True:
            command = Prompt.ask("Command")
            if command.strip() == ":done":
                break
            if command.strip():
                collected_commands.append(command)

        new_commands = collected_commands or None

    update_result = storage.update_workflow(name, new_description, new_commands)
    _print_result(update_result)
    _raise_for_result(update_result)


@app.command("delete", context_settings=COMMAND_CONTEXT)
def delete_workflow(name: str = typer.Argument(..., help="Workflow name to delete.")):
    """Delete a saved workflow."""
    result = storage.delete_workflow(name)
    _print_result(result)
    _raise_for_result(result)


@app.command("clearhistory", context_settings=COMMAND_CONTEXT)
def clearhistory(
    yes: bool = typer.Option(False, "--yes", "-y", help="Clear without asking for confirmation."),
):
    """Clear every saved workflow from Redo storage."""
    if not yes and not Confirm.ask("Clear all saved workflows?", default=False):
        ui.print_warning("clear history cancelled")
        raise typer.Exit(code=1)

    result = storage.clear_workflows()
    _print_result(result)
    _raise_for_result(result)


@app.command("guide", context_settings=COMMAND_CONTEXT)
def guide():
    """Show the Redo quick-start guide."""
    ui.show_guide()


@app.command("lint", context_settings=COMMAND_CONTEXT)
def lint_workflows():
    """Check saved workflows for common mistakes."""
    result = storage.load_workflows()
    if result["code"] != 0:
        _print_result(result)
        raise typer.Exit(code=1)

    lint_result = inspector.lint_workflows(result["data"])
    ui.show_lint_report(lint_result)
    _raise_for_result(lint_result)


@app.command("copy", context_settings=COMMAND_CONTEXT)
def copy_workflow(
    source: str = typer.Argument(..., help="Workflow to copy."),
    target: str = typer.Argument(..., help="New workflow name."),
):
    """Copy a workflow into a new workflow name."""
    result = storage.copy_workflow(source, target)
    _print_result(result)
    _raise_for_result(result)


@app.command("rename", context_settings=COMMAND_CONTEXT)
def rename_workflow(
    old_name: str = typer.Argument(..., help="Current workflow name."),
    new_name: str = typer.Argument(..., help="New workflow name."),
):
    """Rename a saved workflow."""
    result = storage.rename_workflow(old_name, new_name)
    _print_result(result)
    _raise_for_result(result)


@app.command("run", context_settings=COMMAND_CONTEXT)
def run_workflow(
    name: str = typer.Argument(..., help="Workflow name to run."),
    dry: bool = typer.Option(False, "--dry", help="Preview commands without running them."),
    show_output: bool = typer.Option(False, "--show-output", help="Show captured output after successful commands."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Let commands print directly while they run."),
    shell: str = typer.Option("auto", "--shell", help="Shell to use: auto, powershell, cmd, bash, sh, system."),
):
    """Run a saved workflow."""
    result = storage.get_workflow(name)
    if result["code"] != 0:
        _print_result(result)
        raise typer.Exit(code=1)

    commands = placeholders.process_commands(result["data"].get("commands", []))
    if dry:
        ui.show_commands(commands)

    output_mode = "verbose" if verbose else "summary" if show_output else "hidden"
    run_result = runner.run_workflow_commands(commands, dry_run=dry, output_mode=output_mode, shell_name=shell)
    _print_result(run_result)

    if run_result["code"] == 0 and not dry:
        increment_result = storage.increment_runs(name)
        if increment_result["code"] != 0:
            _print_result(increment_result)
            raise typer.Exit(code=1)
    elif run_result["code"] != 0:
        raise typer.Exit(code=1)


@app.command("stats", context_settings=COMMAND_CONTEXT)
def stats():
    """Show workflow usage stats."""
    result = storage.load_workflows()
    if result["code"] != 0:
        _print_result(result)
        raise typer.Exit(code=1)

    ui.show_stats(result["data"])


@app.command("update", context_settings=COMMAND_CONTEXT)
def update(
    check_only: bool = typer.Option(False, "--check-only", help="Only check for updates; do not install."),
):
    """Check for a newer Redo version and install it when available."""
    result = update_checker.check_for_update(VERSION, force=True)
    ui.show_update_result(result)

    if check_only or not result.get("data", {}).get("update_available"):
        raise typer.Exit(code=0)

    ui.print_warning("Installing the latest Redo release with pip...")
    completed = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "redo-cli"])
    if completed.returncode == 0:
        ui.print_success("Redo update installed. Restart your terminal if the old command is still cached.")
    else:
        ui.print_error("Redo update failed. Try running: pip install --upgrade redo-cli")
        raise typer.Exit(code=completed.returncode)

    raise typer.Exit(code=0)


@app.command("path", context_settings=COMMAND_CONTEXT)
def workflow_path():
    """Show where Redo stores workflows for this directory."""
    typer.echo(str(storage.DATA_FILE.resolve()))


@app.command("folder", context_settings=COMMAND_CONTEXT)
def workflow_folder(
    open_folder: bool = typer.Option(False, "--open", help="Open the folder in the system file browser."),
):
    """Show or open the Redo storage folder."""
    folder = storage.DATA_FILE.parent.resolve()
    if open_folder:
        try:
            if os.name == "nt":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", str(folder)], check=False)
            else:
                subprocess.run(["xdg-open", str(folder)], check=False)
        except OSError as error:
            ui.print_error(f"could not open folder: {error}")
            raise typer.Exit(code=1)

    typer.echo(str(folder))


@app.command("export", context_settings=COMMAND_CONTEXT)
def export_workflows(destination: str = typer.Argument(..., help="JSON file to write.")):
    """Export workflows to a JSON backup file."""
    result = storage.export_workflows(destination)
    _print_result(result)
    _raise_for_result(result)


@app.command("backup", context_settings=COMMAND_CONTEXT)
def backup_workflows(
    directory: Path = typer.Option(Path("."), "--dir", help="Directory for the timestamped backup file."),
):
    """Export workflows to a timestamped backup file."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    destination = directory / f"redo-workflows-{timestamp}.json"
    result = storage.export_workflows(destination)
    _print_result(result)
    _raise_for_result(result)


@app.command("import", context_settings=COMMAND_CONTEXT)
def import_workflows(
    source: str = typer.Argument(..., help="JSON workflow file to import."),
    replace: bool = typer.Option(False, "--replace", help="Replace existing workflows."),
):
    """Import workflows from a JSON file."""
    result = storage.import_workflows(source, replace=replace)
    _print_result(result)
    _raise_for_result(result)


@app.command("doctor", context_settings=COMMAND_CONTEXT)
def doctor():
    """Check workflow storage and flag risky saved commands."""
    result = storage.load_workflows()
    if result["code"] != 0:
        _print_result(result)
        raise typer.Exit(code=1)

    workflows = result["data"]
    dangerous_commands = []
    placeholder_names = set()

    for name, workflow in workflows.items():
        for command in workflow.get("commands", []):
            placeholder_names.update(placeholders.find_placeholders(command))
            if runner.is_dangerous_command(command):
                dangerous_commands.append((name, command))

    report = {
        "path": str(storage.DATA_FILE.resolve()),
        "exists": storage.DATA_FILE.exists(),
        "total_workflows": len(workflows),
        "total_commands": sum(len(workflow.get("commands", [])) for workflow in workflows.values()),
        "placeholder_count": len(placeholder_names),
        "dangerous_count": len(dangerous_commands),
        "dangerous_commands": dangerous_commands,
    }
    ui.show_doctor_report(report)


@app.command("autofix", context_settings=COMMAND_CONTEXT)
def autofix():
    """Fix common Redo storage problems automatically."""
    result = storage.autofix_storage()
    _print_result(result)

    for fix in result.get("data", {}).get("fixes", []):
        ui.console.print(f"- {fix}")

    _raise_for_result(result)


if __name__ == "__main__":
    app()
