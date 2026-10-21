import pytest
from app.services.skill_runtime import render_skill, validate_schema

def test_render_skill_replaces_input():
    assert render_skill("Hello {{input.name}}", {"name": "Ada"}) == "Hello Ada"

def test_render_skill_supports_nested_input():
    assert render_skill("{{input.user.name}}", {"user": {"name": "Lin"}}) == "Lin"

def test_render_skill_missing_input_fails():
    with pytest.raises(ValueError, match="Missing required skill input"):
        render_skill("{{input.name}}", {})

def test_schema_required_and_type_checks():
    schema = {"required": ["name"], "properties": {"name": {"type": "string"}}}
    with pytest.raises(ValueError, match="Missing required input"):
        validate_schema(schema, {})
    with pytest.raises(ValueError, match="must be string"):
        validate_schema(schema, {"name": 123})
