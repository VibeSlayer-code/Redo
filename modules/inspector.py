from modules import placeholders, runner


def _result(code, status, message, data=None):
    result = {"code": code, "status": status, "message": message}
    if data is not None:
        result["data"] = data
    return result


def _issue(workflow, command, severity, message):
    return {
        "workflow": workflow,
        "command": command,
        "severity": severity,
        "message": message,
    }


def _looks_comma_separated(command):
    lowered = command.lower()
    if "," not in command:
        return False

    segments = [segment.strip().lower() for segment in command.split(",") if segment.strip()]
    command_like_segments = 0
    for segment in segments:
        if segment.startswith(("git ", "npm ", "python ", "pip ", "cd ", "pytest", "pnpm ", "yarn ")):
            command_like_segments += 1

    return command_like_segments >= 2 or lowered.count("git ") >= 2


def lint_workflows(workflows):
    issues = []
    seen_command_chains = {}

    for name, workflow in workflows.items():
        commands = workflow.get("commands", [])
        if not commands:
            issues.append(_issue(name, "-", "warning", "workflow has no commands"))

        normalized_chain = "\n".join(str(command).strip() for command in commands)
        if normalized_chain in seen_command_chains:
            issues.append(
                _issue(
                    name,
                    "-",
                    "info",
                    f"workflow duplicates the command chain from {seen_command_chains[normalized_chain]}",
                )
            )
        elif normalized_chain:
            seen_command_chains[normalized_chain] = name

        for command in commands:
            command = str(command)
            if not command.strip():
                issues.append(_issue(name, command, "warning", "workflow contains an empty command"))
                continue

            if _looks_comma_separated(command):
                issues.append(_issue(name, command, "warning", "command looks comma-separated; enter one command per line"))

            if runner.is_dangerous_command(command):
                issues.append(_issue(name, command, "warning", "command looks dangerous and will require confirmation"))

            for placeholder in placeholders.find_placeholders(command):
                if placeholder.lower() in {"messgae", "mesage", "msg"}:
                    issues.append(_issue(name, command, "info", f"placeholder {{{placeholder}}} may be a typo for {{message}}"))

    if issues:
        return _result(2, "warning", f"found {len(issues)} workflow issue", {"issues": issues})

    return _result(0, "success", "no workflow issues found", {"issues": []})
