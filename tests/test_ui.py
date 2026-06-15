from io import StringIO

from rich.console import Console

from modules import ui


def test_ui_uses_calm_professional_palette():
    assert "cyan" not in ui.BRAND
    assert "magenta" not in ui.NUMBER
    assert ui.PANEL_BORDER == "grey50"
    assert ui.BRAND == "bold steel_blue"


def capture_ui(monkeypatch):
    output = StringIO()
    monkeypatch.setattr(
        ui,
        "console",
        Console(file=output, force_terminal=False, width=100, color_system=None),
    )
    return output


def test_workflows_table_has_clear_title_and_command_counts(monkeypatch):
    output = capture_ui(monkeypatch)

    ui.show_workflows_table(
        {
            "ship": {
                "description": "Commit and push",
                "commands": ["git add .", "git push"],
                "runs": 3,
            }
        }
    )

    rendered = output.getvalue()
    assert "Redo workflows" in rendered
    assert "ship" in rendered
    assert "2 commands" in rendered


def test_help_menu_is_compact_and_grouped(monkeypatch):
    output = capture_ui(monkeypatch)

    ui.show_help_menu("0.1.0")

    rendered = output.getvalue()
    assert "/$$$$$$$" in rendered
    assert "Redo command center" in rendered
    assert "Daily workflow" in rendered
    assert "Utilities" in rendered
    assert "Storage and maintenance" in rendered
    assert "redo <command> --help" in rendered
    assert rendered.count("+") < 40


def test_workflow_details_are_grouped_with_named_header(monkeypatch):
    output = capture_ui(monkeypatch)

    ui.show_workflow_details(
        "ship",
        {
            "description": "Commit and push",
            "commands": ["git push"],
            "runs": 1,
        },
    )

    rendered = output.getvalue()
    assert "Workflow: ship" in rendered
    assert "Commit and push" in rendered
    assert "git push" in rendered


def test_info_screen_has_launch_check_credit_and_storage_path(monkeypatch):
    output = capture_ui(monkeypatch)

    ui.show_info("0.1.0", "Vibeslayer-code", storage_path="C:/Redo/workflows.json", animated=False)

    rendered = output.getvalue()
    assert "/$$$$$$$" in rendered
    assert "Launch check" in rendered
    assert "Ready to redo" in rendered
    assert "Vibeslayer-code" in rendered
    assert "C:/Redo/workflows.json" in rendered


def test_estimated_time_saved_weights_developer_commands():
    assert ui._estimate_command_saved_seconds("npm install") > ui._estimate_command_saved_seconds("echo ok")
    assert ui._estimate_command_saved_seconds('git commit -m "{message}"') > ui._estimate_command_saved_seconds("git add .")
    assert ui._estimate_workflow_saved_seconds(
        {"commands": ["npm install", 'git commit -m "{message}"'], "runs": 2}
    ) == 112


def test_stats_formats_estimated_time_saved(monkeypatch):
    output = capture_ui(monkeypatch)

    ui.show_stats(
        {
            "ship": {
                "description": "Commit and push",
                "commands": ["git add .", "git commit", "git push"],
                "runs": 5,
            }
        }
    )

    rendered = output.getvalue()
    assert "Redo stats" in rendered
    assert "Estimated time saved" in rendered
    assert "2m 10s" in rendered


def test_stats_handles_manually_corrupted_run_counts(monkeypatch):
    output = capture_ui(monkeypatch)

    ui.show_stats(
        {
            "odd": {
                "description": "Edited by hand",
                "commands": ["git push"],
                "runs": "many",
            }
        }
    )

    rendered = output.getvalue()
    assert "Redo stats" in rendered
    assert "Total runs" in rendered
    assert "0" in rendered


def test_doctor_report_summarizes_health(monkeypatch):
    output = capture_ui(monkeypatch)

    ui.show_doctor_report(
        {
            "path": "C:/redo/files/workflows.json",
            "exists": True,
            "total_workflows": 1,
            "total_commands": 1,
            "placeholder_count": 0,
            "dangerous_count": 1,
            "dangerous_commands": [("reset", "git reset --hard HEAD")],
        }
    )

    rendered = output.getvalue()
    assert "Health check" in rendered
    assert "Needs attention" in rendered
    assert "Dangerous commands" in rendered
