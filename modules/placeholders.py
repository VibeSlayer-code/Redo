import os
import re
import shlex

from rich.prompt import Prompt


PLACEHOLDER_PATTERN = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
QUOTED_PLACEHOLDER_PATTERN = re.compile(r"(?P<quote>['\"])\{([A-Za-z_][A-Za-z0-9_]*)\}(?P=quote)")
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


def _normalize_placeholder_value(value):
    normalized = str(value).replace("\r", " ").replace("\n", " ").replace("\x00", "")
    return " ".join(normalized.split())


def _quote_cmd_value(value):
    escaped = []
    for character in value:
        if character in '^&|<>()%!"':
            escaped.append(f"^{character}")
        else:
            escaped.append(character)
    return f'"{"".join(escaped)}"'


def _escape_cmd_value(value):
    return _quote_cmd_value(value)[1:-1]


def _escape_posix_double_quoted_value(value):
    escaped = []
    for character in value:
        if character in '\\$`"':
            escaped.append(f"\\{character}")
        else:
            escaped.append(character)
    return "".join(escaped)


def _escape_posix_single_quoted_value(value):
    return value.replace("'", "'\\''")


def _shell_quote_placeholder_value(value):
    normalized = _normalize_placeholder_value(value)
    if os.name == "nt":
        return _quote_cmd_value(normalized)
    return shlex.quote(normalized)


def _quote_context(text, position):
    quote = None
    escaped = False
    for character in text[:position]:
        if escaped:
            escaped = False
            continue
        if character == "\\" and quote != "'":
            escaped = True
            continue
        if character in "'\"":
            if quote == character:
                quote = None
            elif quote is None:
                quote = character
    return quote


def _placeholder_value_for_context(value, quote):
    normalized = _normalize_placeholder_value(value)
    if quote is None:
        return _shell_quote_placeholder_value(normalized)
    if os.name == "nt":
        return _escape_cmd_value(normalized)
    if quote == "'":
        return _escape_posix_single_quoted_value(normalized)
    return _escape_posix_double_quoted_value(normalized)


def replace_placeholders(text, values):
    def quoted_replacement(match):
        name = match.group(2)
        if name not in values:
            return match.group(0)
        return _shell_quote_placeholder_value(values[name])

    text = QUOTED_PLACEHOLDER_PATTERN.sub(quoted_replacement, text)

    def replacement(match):
        name = match.group(1)
        if name not in values:
            return match.group(0)
        quote = _quote_context(text, match.start())
        return _placeholder_value_for_context(values[name], quote)

    return PLACEHOLDER_PATTERN.sub(replacement, text)


def process_commands(commands):
    names = find_placeholders_in_commands(commands)
    values = collect_placeholder_values(names)
    return [replace_placeholders(command, values) for command in commands]
