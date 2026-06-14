from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme


theme = Theme(
    {
        "brand": "bold steel_blue",
        "muted": "grey58",
        "success": "green4",
        "warning": "dark_orange3",
        "error": "red3",
        "number": "grey82",
        "command": "bright_white",
    }
)
console = Console(theme=theme, highlight=False)

BRAND = "bold steel_blue"
MUTED = "grey58"
SUCCESS = "green4"
WARNING = "dark_orange3"
ERROR = "red3"
NUMBER = "grey82"
PANEL_BORDER = "grey50"
TABLE_BORDER = "grey46"


def _status_line(label, message, style):
    text = Text()
    text.append(f"[{label}] ", style=style)
    text.append(message)
    console.print(text)


def _plural(count, singular, plural=None):
    if count == 1:
        return f"{count} {singular}"
    return f"{count} {plural or singular + 's'}"


def _format_seconds(seconds):
    seconds = int(seconds)
    minutes, remaining_seconds = divmod(seconds, 60)
    hours, remaining_minutes = divmod(minutes, 60)

    parts = []
    if hours:
        parts.append(f"{hours}h")
    if remaining_minutes:
        parts.append(f"{remaining_minutes}m")
    if remaining_seconds or not parts:
        parts.append(f"{remaining_seconds}s")

    return " ".join(parts)


def _metadata_table(rows):
    table = Table.grid(padding=(0, 2))
    table.add_column(style=MUTED, no_wrap=True)
    table.add_column()

    for label, value in rows:
        table.add_row(label, str(value))

    return table


def print_success(message):
    _status_line("SUCCESS", message, SUCCESS)


def print_error(message):
    _status_line("ERROR", message, ERROR)


def print_warning(message):
    _status_line("WARNING", message, WARNING)


def show_banner():
    console.print(
        Panel.fit(
            Text.assemble(
                ("Redo\n", BRAND),
                ("Bookmarks for terminal workflows.", MUTED),
            ),
            border_style=BRAND,
            box=box.ROUNDED,
        )
    )


def show_workflows_table(workflows):
    if not workflows:
        console.print(
            Panel(
                Text("No workflows saved yet.", style=MUTED),
                title="Redo workflows",
                border_style=PANEL_BORDER,
                box=box.ROUNDED,
            )
        )
        return

    table = Table(
        title="Redo workflows",
        box=box.ROUNDED,
        border_style=TABLE_BORDER,
        header_style=BRAND,
        show_lines=False,
    )
    table.add_column("Name", style="bold", no_wrap=True)
    table.add_column("Description", overflow="fold")
    table.add_column("Commands", justify="right", no_wrap=True)
    table.add_column("Runs", justify="right", style=NUMBER, no_wrap=True)

    for name, workflow in sorted(workflows.items()):
        command_count = len(workflow.get("commands", []))
        table.add_row(
            name,
            workflow.get("description", "") or "-",
            _plural(command_count, "command"),
            str(workflow.get("runs", 0)),
        )

    console.print(table)


def show_workflow_details(name, workflow):
    commands = workflow.get("commands", [])
    metadata = _metadata_table(
        [
            ("Description", workflow.get("description", "") or "-"),
            ("Commands", _plural(len(commands), "command")),
            ("Runs", workflow.get("runs", 0)),
        ]
    )

    console.print(
        Panel(
            metadata,
            title=f"Workflow: {name}",
            border_style=PANEL_BORDER,
            box=box.ROUNDED,
            expand=False,
        )
    )
    show_commands(commands)


def show_commands(commands):
    if not commands:
        console.print(
            Panel(
                Text("No commands in this workflow.", style=MUTED),
                title="Commands",
                border_style=PANEL_BORDER,
                box=box.ROUNDED,
            )
        )
        return

    table = Table(
        title="Commands",
        box=box.SIMPLE_HEAVY,
        header_style=BRAND,
        show_edge=False,
    )
    table.add_column("#", justify="right", style=MUTED, no_wrap=True)
    table.add_column("Command")

    for index, command in enumerate(commands, start=1):
        syntax = Syntax(command, "bash", theme="ansi_dark", word_wrap=True)
        table.add_row(str(index), syntax)

    console.print(table)


def show_stats(workflows):
    total_workflows = len(workflows)
    total_runs = sum(int(workflow.get("runs", 0)) for workflow in workflows.values())
    total_commands = sum(len(workflow.get("commands", [])) for workflow in workflows.values())
    total_commands_run = sum(
        len(workflow.get("commands", [])) * int(workflow.get("runs", 0))
        for workflow in workflows.values()
    )
    estimated_seconds_saved = total_commands_run * 5
    most_used = "-"

    if workflows:
        most_used_name, most_used_workflow = max(
            workflows.items(),
            key=lambda item: int(item[1].get("runs", 0)),
        )
        most_used = f"{most_used_name} ({_plural(int(most_used_workflow.get('runs', 0)), 'run')})"

    summary = _metadata_table(
        [
            ("Total workflows", total_workflows),
            ("Saved commands", total_commands),
            ("Total runs", total_runs),
            ("Most used workflow", most_used),
            ("Estimated time saved", _format_seconds(estimated_seconds_saved)),
        ]
    )
    console.print(
        Panel(
            summary,
            title="Redo stats",
            border_style=PANEL_BORDER,
            box=box.ROUNDED,
        )
    )


def show_doctor_report(report):
    has_warnings = report["dangerous_count"] > 0 or not report["exists"]
    health_text = "Needs attention" if has_warnings else "Ready"
    health_style = WARNING if has_warnings else SUCCESS

    headline = Text.assemble(
        ("Status: ", MUTED),
        (health_text, health_style),
    )
    checks = _metadata_table(
        [
            ("Workflow file", report["path"]),
            ("File exists", "yes" if report["exists"] else "no"),
            ("Total workflows", report["total_workflows"]),
            ("Total commands", report["total_commands"]),
            ("Placeholder fields", report["placeholder_count"]),
            ("Dangerous commands", report["dangerous_count"]),
        ]
    )

    console.print(
        Panel(
            Group(headline, "", checks),
            title="Health check",
            border_style=health_style,
            box=box.ROUNDED,
        )
    )

    if report["dangerous_commands"]:
        table = Table(
            title="Dangerous commands",
            box=box.ROUNDED,
            border_style=WARNING,
            header_style=WARNING,
        )
        table.add_column("Workflow", style="bold", no_wrap=True)
        table.add_column("Command")
        for name, command in report["dangerous_commands"]:
            table.add_row(name, command)
        console.print(table)
