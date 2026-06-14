import subprocess

from modules import runner


def test_is_dangerous_command_detects_known_patterns():
    assert runner.is_dangerous_command("rm -rf dist") is True
    assert runner.is_dangerous_command("git reset --hard HEAD") is True
    assert runner.is_dangerous_command("echo safe") is False


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


def test_run_command_captures_output_instead_of_streaming(monkeypatch):
    run_kwargs = {}

    def fake_run(command, **kwargs):
        run_kwargs.update(kwargs)
        return subprocess.CompletedProcess(command, 0, stdout="quiet output", stderr="")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    result = runner.run_command("echo hello")

    assert result["code"] == 0
    assert run_kwargs["capture_output"] is True
    assert run_kwargs["text"] is True
    assert result["data"]["stdout"] == "quiet output"


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
