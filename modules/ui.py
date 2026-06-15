import time

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme


ASCII_BANNER = r"""
 /$$$$$$$                  /$$
| $$__  $$                | $$
| $$  \ $$  /$$$$$$   /$$$$$$$  /$$$$$$
| $$$$$$$/ /$$__  $$ /$$__  $$ /$$__  $$
| $$__  $$| $$$$$$$$| $$  | $$| $$  \ $$
| $$  \ $$| $$_____/| $$  | $$| $$  | $$
| $$  | $$|  $$$$$$$|  $$$$$$$|  $$$$$$/
|__/  |__/ \_______/ \_______/ \______/
""".strip("\n")

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
BANNER_START = "#6f86a8"
BANNER_END = "#b39ddb"


def _hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _blend(start, end, ratio):
    return tuple(round(start[index] + (end[index] - start[index]) * ratio) for index in range(3))


def _gradient_text(text, start_color=BANNER_START, end_color=BANNER_END):
    start = _hex_to_rgb(start_color)
    end = _hex_to_rgb(end_color)
    lines = text.splitlines()
    total = max(len(lines) - 1, 1)
    output = Text()

    for index, line in enumerate(lines):
        color = _rgb_to_hex(_blend(start, end, index / total))
        output.append(line, style=f"bold {color}")
        if index != len(lines) - 1:
            output.append("\n")

    return output


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


def _estimate_command_saved_seconds(command):
    normalized = " ".join(command.lower().split())
    seconds = 6

    if normalized.startswith(("echo ", "pwd", "ls", "dir")):
        seconds = 4
    elif "npm install" in normalized or "pnpm install" in normalized or "yarn install" in normalized:
        seconds = 34
    elif "pip install" in normalized or "poetry install" in normalized:
        seconds = 30
    elif normalized.startswith("git commit"):
        seconds = 10
    elif normalized.startswith(("git push", "git pull", "git fetch")):
        seconds = 10
    elif any(tool in normalized for tool in ("docker ", "pytest", "npm run", "pnpm run", "yarn run")):
        seconds = 18

    if "{" in command and "}" in command:
        seconds += 12
    if len(command) > 60:
        seconds += 6
    if any(separator in command for separator in ("&&", "||", "|", ";")):
        seconds += 5

    return min(seconds, 45)


def _estimate_workflow_saved_seconds(workflow):
    runs = int(workflow.get("runs", 0))
    commands = workflow.get("commands", [])
    return sum(_estimate_command_saved_seconds(command) for command in commands) * runs


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
    console.print(Align.center(_gradient_text(ASCII_BANNER)))
    console.print(Align.center(Text("Bookmarks for terminal workflows.", style=MUTED)))
    console.print(Align.center(Text("Run redo --help for commands or redo --info.", style=MUTED)))


def _show_info_animation():
    if not console.is_terminal:
        return

    steps = ["checking storage", "loading commands", "warming shortcuts", "ready"]
    with Live(console=console, refresh_per_second=12, transient=True) as live:
        for step in steps:
            live.update(
                Panel(
                    Spinner("line", text=Text(f"Redo launch check: {step}", style=BRAND), style=BRAND),
                    border_style=PANEL_BORDER,
                    box=box.ROUNDED,
                )
            )
            time.sleep(0.16)


def show_info(version, credit, animated=False):
    if animated:
        _show_info_animation()

    launch = Table.grid(padding=(0, 2))
    launch.add_column(style=SUCCESS, no_wrap=True)
    launch.add_column()
    launch.add_row("Storage", "Ready")
    launch.add_row("Commands", "Ready")
    launch.add_row("Status", "Ready to redo")

    metadata = _metadata_table(
        [
            ("Version", version),
            ("Credit", credit),
            ("Storage", "redo path"),
            ("Guide", "redo guide"),
        ]
    )

    console.print(Align.center(_gradient_text(ASCII_BANNER)))
    console.print(
        Panel(
            Group(
                Text("Ready to turn repeated terminal work into one command.", style=MUTED),
                "",
                Panel(launch, title="Launch check", border_style=SUCCESS, box=box.ROUNDED),
                "",
                metadata,
            ),
            title="Redo info",
            border_style=PANEL_BORDER,
            box=box.ROUNDED,
        )
    )


def show_help_menu(version):
    console.print(Align.center(_gradient_text(ASCII_BANNER)))
    console.print(Align.center(Text("Bookmarks for terminal workflows.", style=MUTED)))

    commands = Table(
        title="Redo command center",
        box=box.ROUNDED,
        border_style=TABLE_BORDER,
        header_style=BRAND,
        show_lines=False,
        expand=True,
    )
    commands.add_column("Section", style=BRAND, no_wrap=True, width=23)
    commands.add_column("Commands", no_wrap=True, width=28)
    commands.add_column("Purpose", ratio=1)
    commands.add_row(
        "Daily workflow",
        "redo new <name>\nredo run <name>\nredo run <name> --dry\nredo list",
        "Create and run workflows.",
    )
    commands.add_row(
        "Utilities",
        "redo show <name>\nredo search <query>\nredo copy <src> <target>\nredo rename <old> <new>\nredo delete <name>",
        "Find and manage workflows.",
    )
    commands.add_row(
        "Storage and maintenance",
        "redo path\nredo doctor\nredo autofix\nredo export <file>\nredo import <file>\nredo clearhistory",
        "Repair, back up, restore.",
    )
    commands.add_row("--", "redo guide\nredo --info\nredo <command> --help", f"Guide, version {version}, help.")

    console.print(commands)
    console.print(Align.center(Text("Tip: placeholders look like {message} and are filled when you run a workflow.", style=MUTED)))


def show_guide():
    intro = Text.assemble(
        ("Redo guide\n", BRAND),
        ("Save repeated terminal workflows once. Run them again with one command.", MUTED),
    )

    basics = Table.grid(padding=(0, 2))
    basics.add_column(style=MUTED, no_wrap=True)
    basics.add_column()
    basics.add_row("Create", "redo new ship")
    basics.add_row("Run", "redo run ship")
    basics.add_row("Preview", "redo run ship --dry")
    basics.add_row("Inspect", "redo list  |  redo show ship")

    example = Syntax(
        'Description: Commit and push code\n'
        'Command: git add .\n'
        'Command: git commit -m "{message}"\n'
        'Command: git push\n'
        'Command: :done',
        "text",
        theme="ansi_dark",
        word_wrap=True,
    )

    placeholders = Table(
        title="Placeholders",
        box=box.ROUNDED,
        border_style=TABLE_BORDER,
        header_style=BRAND,
    )
    placeholders.add_column("Pattern", no_wrap=True)
    placeholders.add_column("What happens")
    placeholders.add_row("{message}", "Redo asks once, then inserts the value everywhere.")
    placeholders.add_row("{project_name}", "Names must use letters, numbers, and underscores.")

    warnings = Table(
        title="Warnings",
        box=box.ROUNDED,
        border_style=TABLE_BORDER,
        header_style=BRAND,
    )
    warnings.add_column("Tip", no_wrap=True)
    warnings.add_column("Why it matters")
    warnings.add_row("One command per prompt", "Do not separate commands with commas.")
    warnings.add_row('Use git commit -m "{message}"', "Git needs -m for commit messages.")
    warnings.add_row("Use --dry first", "Preview before running risky workflows.")

    console.print(Panel(intro, title="Redo guide", border_style=PANEL_BORDER, box=box.ROUNDED))
    console.print(Panel(Group(basics, "", example), title="Create a workflow", border_style=PANEL_BORDER, box=box.ROUNDED))
    console.print(placeholders)
    console.print(warnings)


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
    estimated_seconds_saved = sum(_estimate_workflow_saved_seconds(workflow) for workflow in workflows.values())
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
