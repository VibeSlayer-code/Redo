from modules import templates


def test_builtin_templates_include_developer_workflows():
    available = templates.list_templates()

    assert "ship" in available
    assert "python-test" in available
    assert "node-dev" in available


def test_get_template_returns_independent_copy():
    template = templates.get_template("ship")
    template["commands"].append("echo mutated")

    fresh_template = templates.get_template("ship")

    assert "echo mutated" not in fresh_template["commands"]


def test_get_template_reports_missing_template():
    result = templates.get_template("missing")

    assert result is None
