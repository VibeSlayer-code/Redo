from modules import placeholders


def test_find_placeholders_detects_valid_unique_names_in_order():
    text = 'git commit -m "{message}" && echo {project_name} {message} {1bad} {bad-name}'

    assert placeholders.find_placeholders(text) == ["message", "project_name"]


def test_find_placeholders_in_commands_deduplicates_across_commands():
    commands = [
        "npm create vite@latest {project_name}",
        "cd {project_name}",
        "git commit -m {message}",
    ]

    assert placeholders.find_placeholders_in_commands(commands) == ["project_name", "message"]


def test_replace_placeholders_replaces_all_occurrences(monkeypatch):
    monkeypatch.setattr(placeholders.os, "name", "posix")
    text = "cd {project_name} && echo {project_name}"

    result = placeholders.replace_placeholders(text, {"project_name": "my-app"})

    assert result == "cd my-app && echo my-app"


def test_placeholder_values_are_shell_quoted(monkeypatch):
    monkeypatch.setattr(placeholders.os, "name", "posix")
    text = "git commit -m {message}"

    result = placeholders.replace_placeholders(text, {"message": 'ok" && echo hacked'})

    assert result == "git commit -m 'ok\" && echo hacked'"


def test_placeholder_replacement_handles_existing_quotes(monkeypatch):
    monkeypatch.setattr(placeholders.os, "name", "posix")
    text = 'git commit -m "{message}"'

    result = placeholders.replace_placeholders(text, {"message": 'ok" && echo hacked'})

    assert result == "git commit -m 'ok\" && echo hacked'"


def test_embedded_placeholder_inside_double_quotes_escapes_shell_syntax(monkeypatch):
    monkeypatch.setattr(placeholders.os, "name", "posix")

    result = placeholders.replace_placeholders('echo "prefix {value}"', {"value": "$(touch pwned)"})

    assert result == 'echo "prefix \\$(touch pwned)"'


def test_embedded_placeholder_inside_single_quotes_escapes_single_quotes(monkeypatch):
    monkeypatch.setattr(placeholders.os, "name", "posix")

    result = placeholders.replace_placeholders("echo 'prefix {value}'", {"value": "can't"})

    assert result == "echo 'prefix can'\\''t'"


def test_placeholder_values_prevent_shell_expansion(monkeypatch):
    monkeypatch.setattr(placeholders.os, "name", "posix")

    assert placeholders.replace_placeholders("echo {value}", {"value": "$HOME"}) == "echo '$HOME'"
    assert placeholders.replace_placeholders("echo {value}", {"value": "*.py"}) == "echo '*.py'"
    assert placeholders.replace_placeholders("rm {target}", {"target": "-rf dist"}) == "rm '-rf dist'"
    assert placeholders.replace_placeholders("echo {value}", {"value": "${PATH}"}) == "echo '${PATH}'"


def test_windows_placeholder_values_escape_cmd_metacharacters(monkeypatch):
    monkeypatch.setattr(placeholders.os, "name", "nt")

    result = placeholders.replace_placeholders("echo {value}", {"value": "%PATH% & whoami"})

    assert result == 'echo "^%PATH^% ^& whoami"'


def test_process_commands_strips_newlines_from_placeholder_values(monkeypatch):
    monkeypatch.setattr(placeholders.os, "name", "posix")
    monkeypatch.setattr(placeholders, "prompt", lambda label: "first\nsecond")

    result = placeholders.process_commands(["echo {message}"])

    assert result == ["echo 'first second'"]


def test_process_commands_prompts_once_per_placeholder(monkeypatch):
    monkeypatch.setattr(placeholders.os, "name", "posix")
    prompts = []

    def fake_prompt(label):
        prompts.append(label)
        return "my-app"

    monkeypatch.setattr(placeholders, "prompt", fake_prompt)

    result = placeholders.process_commands(
        [
            "npm create vite@latest {project_name}",
            "cd {project_name}",
            "npm install",
        ]
    )

    assert prompts == ["project_name"]
    assert result == [
        "npm create vite@latest my-app",
        "cd my-app",
        "npm install",
    ]
