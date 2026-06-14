import re
import subprocess

from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Confirm
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text


console = Console(highlight=False)

DANGEROUS_PATTERNS = [
    r"\brm\s+-[a-z]*r[a-z]*f\b",
    r"\brm\s+-[a-z]*f[a-z]*r\b",
    r"\bdel\s+/s\b",
    r"\brd\s+/s\b",
    r"\brmdir\s+/s\b",
    r"\bremove-item\b(?=.*-recurse\b)(?=.*-force\b)",
    r"\bformat\b",
    r"\bsudo\b",
    r"\bgit\s+reset\s+--hard\b",
]

STATUS_PENDING = "Pending"
STATUS_RUNNING = "Running"
STATUS_DONE = "Done"
STATUS_FAILED = "Failed"
STATUS_SKIPPED = "Skipped"
SPINNER_NAME = "line"


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
    return any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in DANGEROUS_PATTERNS)


def _status_style(status):
    if status == STATUS_DONE:
        return "bold green"
    if status == STATUS_RUNNING:
        return "bold steel_blue"
    if status == STATUS_FAILED:
        return "bold red"
    if status == STATUS_SKIPPED:
        return "yellow"
    return "dim"


def _workflow_table(commands, statuses):
    table = Table(
        box=box.ROUNDED,
        border_style="grey46",
        header_style="bold steel_blue",
        expand=True,
    )
    table.add_column("#", justify="right", style="dim", no_wrap=True)
    table.add_column("Command", overflow="fold")
    table.add_column("Status", justify="right", no_wrap=True)

    for index, command in enumerate(commands, start=1):
        status = statuses[index - 1]
        table.add_row(str(index), command, Text(status, style=_status_style(status)))

    return table


def _workflow_view(commands, statuses):
    loader = Spinner(
        SPINNER_NAME,
        text=Text("Your workflow is running, check the status", style="bold steel_blue"),
        style="steel_blue",
    )
    return Panel(
        Group(loader, "", _workflow_table(commands, statuses)),
        title="Workflow status",
        border_style="grey46",
        box=box.ROUNDED,
    )


def _trim_output(output, max_lines=18):
    lines = output.strip().splitlines()
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(["..."] + lines[-max_lines:])


def _extract_git_upstream_hint(command, stderr):
    if command.strip() != "git push":
        return None
    if "has no upstream branch" not in stderr:
        return None

    match = re.search(r"git push --set-upstream origin [^\s]+", stderr)
    if not match:
        return None

    return f"Set the upstream once with: {match.group(0)}"


def _failure_message(command, returncode, stderr):
    hint = _extract_git_upstream_hint(command, stderr)
    if hint:
        return f"command failed with exit code {returncode}. {hint}"
    return f"command failed with exit code {returncode}"


def _show_failure_details(result):
    data = result.get("data", {})
    stderr = data.get("stderr", "").strip()
    stdout = data.get("stdout", "").strip()
    output = stderr or stdout or "No output captured."

    body = Group(
        Text(f"Command: {data.get('command', '-')}", style="bold"),
        Text(f"Exit code: {data.get('returncode', '-')}", style="red"),
        "",
        Text(_trim_output(output)),
    )
    console.print(
        Panel(
            body,
            title="Command failed",
            border_style="red",
            box=box.ROUNDED,
        )
    )


def run_command(command):
    completed = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
    )

    data = {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout or "",
        "stderr": completed.stderr or "",
    }

    if completed.returncode != 0:
        return _result(
            1,
            "error",
            _failure_message(command, completed.returncode, data["stderr"]),
            data,
        )

    return _result(0, "success", "command completed successfully", data)


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
        console.print("[bold yellow]Dangerous command detected:[/bold yellow]")
        for command in dangerous_commands:
            console.print(f"  {command}")

        if not Confirm.ask("Continue anyway?", default=False):
            return _result(2, "warning", "workflow cancelled by user")

    statuses = [STATUS_PENDING for _ in commands]
    failed_result = None

    with Live(
        _workflow_view(commands, statuses),
        console=console,
        refresh_per_second=8,
    ) as live:
        for index, command in enumerate(commands):
            statuses[index] = STATUS_RUNNING
            live.update(_workflow_view(commands, statuses))

            result = run_command(command)
            if result["code"] != 0:
                statuses[index] = STATUS_FAILED
                for remaining_index in range(index + 1, len(statuses)):
                    statuses[remaining_index] = STATUS_SKIPPED
                live.update(_workflow_view(commands, statuses))
                failed_result = result
                break

            statuses[index] = STATUS_DONE
            live.update(_workflow_view(commands, statuses))

    if failed_result is not None:
        console.print()
        _show_failure_details(failed_result)
        return failed_result

    return _result(
        0,
        "success",
        "workflow completed successfully",
        {"dry_run": False, "commands": commands},
    )
