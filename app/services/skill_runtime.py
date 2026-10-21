import re
from typing import Any

_PLACEHOLDER = re.compile(r"\{\{\s*input\.([a-zA-Z_][a-zA-Z0-9_.]*)\s*\}\}")

def _lookup(data: dict[str, Any], dotted_key: str) -> Any:
    value: Any = data
    for part in dotted_key.split("."):
        if not isinstance(value, dict) or part not in value:
            raise ValueError(f"Missing required skill input: {dotted_key}")
        value = value[part]
    return value

def render_skill(content: str, inputs: dict[str, Any]) -> str:
    """Safe MVP renderer: substitutes values only; never executes skill text as code."""
    def replace(match: re.Match) -> str:
        value = _lookup(inputs, match.group(1))
        if isinstance(value, (dict, list)):
            import json
            return json.dumps(value, ensure_ascii=False)
        return str(value)
    return _PLACEHOLDER.sub(replace, content)

def validate_schema(schema: dict, inputs: dict) -> None:
    """Small JSON Schema subset for required/type checks; use jsonschema for full validation."""
    required = schema.get("required", [])
    for key in required:
        if key not in inputs:
            raise ValueError(f"Missing required input: {key}")
    types = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "object": dict, "array": list}
    for key, spec in schema.get("properties", {}).items():
        expected_type = spec.get("type")
        if key not in inputs or expected_type not in types:
            continue

        value = inputs[key]
        matches_type = isinstance(value, types[expected_type])
        # Python treats bool as a subclass of int, but JSON Schema does not.
        if expected_type in {"integer", "number"} and isinstance(value, bool):
            matches_type = False
        if not matches_type:
            raise ValueError(f"Input '{key}' must be {expected_type}")
