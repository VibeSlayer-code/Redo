import subprocess

from modules import runner


def test_is_dangerous_command_detects_known_patterns():
    assert runner.is_dangerous_command("rm -rf dist") is True
    assert runner.is_dangerous_command("git reset --hard HEAD") is True
    assert runner.is_dangerous_command("echo safe") is False


def test_run_workflow_commands_dry_run_does_not_execute(monkeypatch):
    calls = []
    monkeypatch.setattr(runner.subprocess, "run", lambda *args, **kwargs: calls.append(args))

    result = runner.run_workflow_commands(["echo hello"], dry_run=True)

    assert result["status"] == "success"
    assert result["data"]["dry_run"] is True
    assert calls == []


def test_run_workflow_commands_stops_on_failure(monkeypatch):
    commands_run = []

    def fake_run(command, shell):
        commands_run.append(command)
        return subprocess.CompletedProcess(command, 1)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    result = runner.run_workflow_commands(["first", "second"])

    assert result["code"] == 1
    assert result["status"] == "error"
    assert commands_run == ["first"]


def test_dangerous_command_requires_confirmation(monkeypatch):
    monkeypatch.setattr(runner.Confirm, "ask", lambda *args, **kwargs: False)

    result = runner.run_workflow_commands(["sudo reboot"])

    assert result["code"] == 2
    assert result["status"] == "warning"
