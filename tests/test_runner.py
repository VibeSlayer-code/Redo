import subprocess
from io import StringIO

from rich.console import Console

from modules import runner


def test_is_dangerous_command_detects_known_patterns():
    assert runner.is_dangerous_command("rm -rf dist") is True
    assert runner.is_dangerous_command("rm -fr dist") is True
    assert runner.is_dangerous_command("rm -r -f dist") is True
    assert runner.is_dangerous_command("rm --recursive --force dist") is True
    assert runner.is_dangerous_command("rm --force --recursive dist") is True
    assert runner.is_dangerous_command("rm -r --force dist") is True
    assert runner.is_dangerous_command("rm -f --recursive dist") is True
    assert runner.is_dangerous_command("echo ok && rm -rf dist") is True
    assert runner.is_dangerous_command("cd tmp; rm -fr dist") is True
    assert runner.is_dangerous_command("true || rm --recursive --force dist") is True
    assert runner.is_dangerous_command("Remove-Item -Recurse -Force dist") is True
    assert runner.is_dangerous_command("rd /s /q dist") is True
    assert runner.is_dangerous_command("git reset --hard HEAD") is True
    assert runner.is_dangerous_command("dd if=/dev/zero of=/dev/sda") is True
    assert runner.is_dangerous_command("mkfs.ext4 /dev/sda") is True
    assert runner.is_dangerous_command("echo safe") is False


def test_runner_status_table_uses_calm_palette():
    assert "cyan" not in runner._status_style(runner.STATUS_RUNNING)
    table = runner._workflow_table(["echo ok"], [runner.STATUS_PENDING])
    assert table.border_style == "grey46"
    assert table.header_style == "bold steel_blue"
    assert table.title is None


def test_runner_workflow_view_uses_loader_status_message():
    output = StringIO()
    test_console = Console(file=output, force_terminal=False, width=100, color_system=None)

    test_console.print(runner._workflow_view(["echo ok"], [runner.STATUS_RUNNING]))

    rendered = output.getvalue()
    assert "Your workflow is running, check the status" in rendered
    assert "Running your workflow" not in rendered
    assert runner.SPINNER_NAME == "line"


def test_run_workflow_commands_dry_run_does_not_execute(monkeypatch):
    calls = []
    monkeypatch.setattr(runner.subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs)))

    result = runner.run_workflow_commands(["echo hello"], dry_run=True)

    assert result["status"] == "success"
    assert result["data"]["dry_run"] is True
    assert calls == []


def test_run_workflow_commands_stops_on_failure(monkeypatch):
    commands_run = []

    def fake_run(command, **kwargs):
        commands_run.append(command)
        return subprocess.CompletedProcess(command, 1, stdout="nope", stderr="failed hard")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    result = runner.run_workflow_commands(["first", "second"])

    assert result["code"] == 1
    assert result["status"] == "error"
    assert commands_run == ["first"]
    assert result["data"]["stderr"] == "failed hard"
    assert result["data"]["stdout"] == "nope"


def test_dangerous_command_requires_confirmation(monkeypatch):
    monkeypatch.setattr(runner.Confirm, "ask", lambda *args, **kwargs: False)

    result = runner.run_workflow_commands(["sudo reboot"])

    assert result["code"] == 2
    assert result["status"] == "warning"


def test_run_command_captures_output_and_sets_timeout(monkeypatch):
    run_kwargs = {}

    def fake_run(command, **kwargs):
        run_kwargs.update(kwargs)
        return subprocess.CompletedProcess(command, 0, stdout="quiet output", stderr="")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    result = runner.run_command("echo hello")

    assert result["code"] == 0
    assert run_kwargs["capture_output"] is True
    assert run_kwargs["text"] is True
    assert run_kwargs["timeout"] == runner.COMMAND_TIMEOUT_SECONDS
    assert result["data"]["stdout"] == "quiet output"


def test_run_command_handles_timeout(monkeypatch):
    def fake_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"], output=b"partial", stderr=b"slow")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    result = runner.run_command("sleep forever")

    assert result["code"] == 1
    assert result["status"] == "error"
    assert "timed out" in result["message"]
    assert result["data"]["stdout"] == "partial"
    assert result["data"]["stderr"] == "slow"


def test_git_push_without_upstream_returns_helpful_hint(monkeypatch):
    stderr = """
fatal: The current branch master has no upstream branch.
    git push --set-upstream origin master
"""

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 128, stdout="", stderr=stderr)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    result = runner.run_command("git push")

    assert result["code"] == 1
    assert "git push --set-upstream origin master" in result["message"]
