import re

from rich.prompt import Prompt


PLACEHOLDER_PATTERN = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
prompt = Prompt.ask


def find_placeholders(text):
    placeholders = []
    seen = set()

    for match in PLACEHOLDER_PATTERN.finditer(text):
        name = match.group(1)
        if name not in seen:
            placeholders.append(name)
            seen.add(name)

    return placeholders


def find_placeholders_in_commands(commands):
    placeholders = []
    seen = set()

    for command in commands:
        for name in find_placeholders(command):
            if name not in seen:
                placeholders.append(name)
                seen.add(name)

    return placeholders


def collect_placeholder_values(placeholders):
    return {name: prompt(name) for name in placeholders}


def replace_placeholders(text, values):
    def replacement(match):
        name = match.group(1)
        return str(values.get(name, match.group(0)))

    return PLACEHOLDER_PATTERN.sub(replacement, text)


def process_commands(commands):
    names = find_placeholders_in_commands(commands)
    values = collect_placeholder_values(names)
    return [replace_placeholders(command, values) for command in commands]
