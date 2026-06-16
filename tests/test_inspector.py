from modules import inspector


def test_lint_workflows_flags_common_mistakes():
    workflows = {
        "git": {
            "description": "",
            "commands": ['git add ., git commit "{message}", git push', "git reset --hard HEAD"],
            "runs": 0,
        },
        "empty": {"description": "", "commands": ["   "], "runs": 0},
    }

    result = inspector.lint_workflows(workflows)

    messages = [issue["message"] for issue in result["data"]["issues"]]
    assert result["code"] == 2
    assert any("comma-separated" in message for message in messages)
    assert any("dangerous" in message for message in messages)
    assert any("empty command" in message for message in messages)


def test_lint_workflows_passes_clean_workflows():
    workflows = {
        "ship": {
            "description": "Commit and push",
            "commands": ["git add .", 'git commit -m "{message}"', "git push"],
            "runs": 1,
        }
    }

    result = inspector.lint_workflows(workflows)

    assert result["code"] == 0
    assert result["data"]["issues"] == []
