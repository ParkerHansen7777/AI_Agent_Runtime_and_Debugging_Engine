
import pytest

from agent_runtime.tools import tool, ToolRegistry


@pytest.fixture
def registry():
    return ToolRegistry()


def test_schema_maps_supported_types(registry):
    @tool
    def example(name: str, age: int, height: float, active: bool):
        """Example tool."""

    registry.register_tool(example)

    schema = registry.get_tool("example").to_schema()

    assert schema["parameters"]["properties"] == {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "height": {"type": "number"},
        "active": {"type": "boolean"},
    }


def test_schema_identifies_required_parameters(registry):
    @tool
    def example(name: str, age: int, greeting: str = "Hello"):
        """Example tool."""

    registry.register_tool(example)

    schema = registry.get_tool("example").to_schema()

    assert schema["parameters"]["required"] == ["name", "age"]


def test_schema_includes_optional_parameters_in_properties(registry):
    @tool
    def example(name: str, greeting: str = "Hello"):
        """Example tool."""

    registry.register_tool(example)

    schema = registry.get_tool("example").to_schema()

    assert "greeting" in schema["parameters"]["properties"]
    assert "greeting" not in schema["parameters"]["required"]


def test_schema_includes_unannotated_parameters(registry):
    @tool
    def example(name: str, limit=10):
        """Example tool."""

    registry.register_tool(example)

    schema = registry.get_tool("example").to_schema()

    assert schema["parameters"]["properties"] == {
        "name": {"type": "string"},
        "limit": {},
    }


def test_schema_handles_tool_without_parameters(registry):
    @tool
    def example():
        """Example tool."""

    registry.register_tool(example)

    schema = registry.get_tool("example").to_schema()

    assert schema["parameters"]["properties"] == {}
    assert schema["parameters"]["required"] == []


def test_schema_disallows_additional_properties(registry):
    @tool
    def example(name: str):
        """Example tool."""

    registry.register_tool(example)

    schema = registry.get_tool("example").to_schema()

    assert schema["parameters"]["additionalProperties"] is False


def test_schema_preserves_name_and_description(registry):
    @tool
    def example(name: str):
        """An example tool description."""

    registry.register_tool(example)

    schema = registry.get_tool("example").to_schema()

    assert schema["name"] == "example"
    assert schema["description"] == "An example tool description."


def test_schema_matches_expected_structure(registry):
    @tool
    def greet(name: str, age: int, greeting: str = "Hello"):
        """Greet someone."""

    registry.register_tool(greet)

    schema = registry.get_tool("greet").to_schema()

    assert schema == {
        "name": "greet",
        "description": "Greet someone.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "greeting": {"type": "string"},
            },
            "required": ["name", "age"],
            "additionalProperties": False,
        },
    }
