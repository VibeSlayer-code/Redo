import re
import subprocess

from rich.console import Console
from rich.prompt import Confirm


console = Console()

DANGEROUS_PATTERNS = [
    r"\brm\s+-[^\n;]*r[^\n;]*f\b",
    r"\bdel\s+/s\b",
    r"\bformat\b",
    r"\bsudo\b",
    r"\bgit\s+reset\s+--hard\b",
]


def _result(code, status, message, data=None):
    result = {
        "code": code,
        "status": status,
        "message": message,
    }
    if data is not None:
        result["data"] = data
    return result


def is_dangerous_command(command):
    normalized = command.strip().lower()
    return any(re.search(pattern, normalized) for pattern in DANGEROUS_PATTERNS)


def run_command(command):
    completed = subprocess.run(command, shell=True)
    if completed.returncode != 0:
        return _result(
            1,
            "error",
            f"command failed with exit code {completed.returncode}",
            {"command": command, "returncode": completed.returncode},
        )

    return _result(0, "success", "command completed successfully", {"command": command})


def run_workflow_commands(commands, dry_run=False):
    if dry_run:
        return _result(
            0,
            "success",
            "dry run completed",
            {"dry_run": True, "commands": commands},
        )

    dangerous_commands = [command for command in commands if is_dangerous_command(command)]
    if dangerous_commands:
        console.print("[yellow]Dangerous command detected:[/yellow]")
        for command in dangerous_commands:
            console.print(f"  {command}")

        if not Confirm.ask("Continue anyway?", default=False):
            return _result(2, "warning", "workflow cancelled by user")

    for command in commands:
        console.print(f"[bold]$[/bold] {command}")
        result = run_command(command)
        if result["code"] != 0:
            return result

    return _result(
        0,
        "success",
        "workflow completed successfully",
        {"dry_run": False, "commands": commands},
    )
