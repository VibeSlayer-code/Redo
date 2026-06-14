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


def test_replace_placeholders_replaces_all_occurrences():
    text = "cd {project_name} && echo {project_name}"

    result = placeholders.replace_placeholders(text, {"project_name": "my-app"})

    assert result == "cd my-app && echo my-app"


def test_process_commands_prompts_once_per_placeholder(monkeypatch):
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
