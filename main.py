import typer
from rich.prompt import Confirm, Prompt

from modules import placeholders, runner, storage, ui


VERSION = "0.1.0"
CREDIT = "credit-vibeslayer"
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


def _offer_first_run_guide():
    if not storage.should_offer_first_run_guide():
        return

    if Confirm.ask("First time using Redo? See the quick guide first?", default=True):
        ui.show_guide()

    result = storage.mark_first_run_guide_seen()
    if result["code"] == 1:
        ui.print_warning(result["message"])


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
        ui.show_info(VERSION, CREDIT)
        raise typer.Exit(code=0)

    if ctx.invoked_subcommand is None:
        ui.show_banner()
        raise typer.Exit(code=0)


@app.command("init", context_settings=COMMAND_CONTEXT)
def init():
    """Create C:/redo/files/workflows.json if needed."""
    result = storage.initialize_file()
    _print_result(result)


@app.command("new", context_settings=COMMAND_CONTEXT)
def new_workflow(name: str = typer.Argument(..., help="Workflow name to create.")):
    """Create a reusable workflow."""
    name_result = storage.validate_workflow_name(name)
    if name_result["code"] != 0:
        _print_result(name_result)
        raise typer.Exit(code=0)

    storage.initialize_file()
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
        raise typer.Exit(code=0)

    result = storage.add_workflow(name, description, commands)
    _print_result(result)


@app.command("list", context_settings=COMMAND_CONTEXT)
def list_workflows():
    """List saved workflows."""
    result = storage.load_workflows()
    if result["code"] == 1:
        ui.print_error(result["message"])
        raise typer.Exit(code=1)

    ui.show_workflows_table(result["data"])


@app.command("search", context_settings=COMMAND_CONTEXT)
def search_workflows(query: str = typer.Argument(..., help="Text to find in workflows.")):
    """Search workflow names, descriptions, and commands."""
    result = storage.find_workflows(query)
    if result["code"] == 1:
        ui.print_error(result["message"])
        raise typer.Exit(code=1)

    ui.show_workflows_table(result["data"])


@app.command("show", context_settings=COMMAND_CONTEXT)
def show_workflow(name: str = typer.Argument(..., help="Workflow name to inspect.")):
    """Show workflow details."""
    result = storage.get_workflow(name)
    if result["code"] != 0:
        _print_result(result)
        raise typer.Exit(code=0 if result["code"] == 2 else 1)

    ui.show_workflow_details(name, result["data"])


@app.command("delete", context_settings=COMMAND_CONTEXT)
def delete_workflow(name: str = typer.Argument(..., help="Workflow name to delete.")):
    """Delete a saved workflow."""
    result = storage.delete_workflow(name)
    _print_result(result)


@app.command("clearhistory", context_settings=COMMAND_CONTEXT)
def clearhistory(
    yes: bool = typer.Option(False, "--yes", "-y", help="Clear without asking for confirmation."),
):
    """Clear every saved workflow from Redo storage."""
    if not yes and not Confirm.ask("Clear all saved workflows?", default=False):
        ui.print_warning("clear history cancelled")
        raise typer.Exit(code=0)

    result = storage.clear_workflows()
    _print_result(result)


@app.command("guide", context_settings=COMMAND_CONTEXT)
def guide():
    """Show the Redo quick-start guide."""
    ui.show_guide()


@app.command("copy", context_settings=COMMAND_CONTEXT)
def copy_workflow(
    source: str = typer.Argument(..., help="Workflow to copy."),
    target: str = typer.Argument(..., help="New workflow name."),
):
    """Copy a workflow into a new workflow name."""
    result = storage.copy_workflow(source, target)
    _print_result(result)


@app.command("rename", context_settings=COMMAND_CONTEXT)
def rename_workflow(
    old_name: str = typer.Argument(..., help="Current workflow name."),
    new_name: str = typer.Argument(..., help="New workflow name."),
):
    """Rename a saved workflow."""
    result = storage.rename_workflow(old_name, new_name)
    _print_result(result)


@app.command("run", context_settings=COMMAND_CONTEXT)
def run_workflow(
    name: str = typer.Argument(..., help="Workflow name to run."),
    dry: bool = typer.Option(False, "--dry", help="Preview commands without running them."),
):
    """Run a saved workflow."""
    result = storage.get_workflow(name)
    if result["code"] != 0:
        _print_result(result)
        raise typer.Exit(code=0 if result["code"] == 2 else 1)

    commands = placeholders.process_commands(result["data"].get("commands", []))
    if dry:
        ui.show_commands(commands)

    run_result = runner.run_workflow_commands(commands, dry_run=dry)
    _print_result(run_result)

    if run_result["code"] == 0 and not dry:
        storage.increment_runs(name)
    elif run_result["code"] == 1:
        raise typer.Exit(code=1)


@app.command("stats", context_settings=COMMAND_CONTEXT)
def stats():
    """Show workflow usage stats."""
    result = storage.load_workflows()
    if result["code"] == 1:
        ui.print_error(result["message"])
        raise typer.Exit(code=1)

    ui.show_stats(result["data"])


@app.command("path", context_settings=COMMAND_CONTEXT)
def workflow_path():
    """Show where Redo stores workflows for this directory."""
    typer.echo(str(storage.DATA_FILE.resolve()))


@app.command("export", context_settings=COMMAND_CONTEXT)
def export_workflows(destination: str = typer.Argument(..., help="JSON file to write.")):
    """Export workflows to a JSON backup file."""
    result = storage.export_workflows(destination)
    _print_result(result)


@app.command("import", context_settings=COMMAND_CONTEXT)
def import_workflows(
    source: str = typer.Argument(..., help="JSON workflow file to import."),
    replace: bool = typer.Option(False, "--replace", help="Replace existing workflows."),
):
    """Import workflows from a JSON file."""
    result = storage.import_workflows(source, replace=replace)
    _print_result(result)


@app.command("doctor", context_settings=COMMAND_CONTEXT)
def doctor():
    """Check workflow storage and flag risky saved commands."""
    result = storage.load_workflows()
    if result["code"] == 1:
        ui.print_error(result["message"])
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


if __name__ == "__main__":
    app()
