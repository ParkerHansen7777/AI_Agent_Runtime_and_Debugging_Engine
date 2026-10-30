
import pytest

from agent_runtime.tools import Tool, ToolRegistry, tool


@tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def test_tool_stores_its_attributes():
    tool_object = Tool(
        name="add",
        description="Add two integers.",
        parameters={"a": int, "b": int},
        func=add,
    )

    assert tool_object.name == "add"
    assert tool_object.description == "Add two integers."
    assert tool_object.parameters == {"a": int, "b": int}
    assert tool_object.func is add


def test_tool_callable_executes_original_function():
    assert add(2, 3) == 5


def test_registry_registers_and_retrieves_tool():
    registry = ToolRegistry()

    registry.register_tool(add)

    retrieved = registry.get_tool("add")

    assert isinstance(retrieved, Tool)
    assert retrieved.name == "add"
    assert retrieved.description == "Add two integers."
    assert retrieved.func is add


def test_registry_rejects_duplicate_names():
    registry = ToolRegistry()

    @tool
    def duplicate_add(a: int, b: int):
        """A duplicate add function."""
        return a + b

    # Give the second function the same registered name.
    duplicate_add.name = "add"

    registry.register_tool(add)

    with pytest.raises(ValueError):
        registry.register_tool(duplicate_add)

    assert registry.get_tool("add").func is add


def test_registry_raises_error_for_missing_tool():
    registry = ToolRegistry()

    with pytest.raises(KeyError):
        registry.get_tool("missing")


def test_registry_lists_registered_tool_names():
    registry = ToolRegistry()

    @tool
    def subtract(a: int, b: int):
        """Subtract two integers."""
        return a - b

    registry.register_tool(add)
    registry.register_tool(subtract)

    assert set(registry.list_tools()) == {"add", "subtract"}


def test_registries_are_independent():
    first_registry = ToolRegistry()
    second_registry = ToolRegistry()

    first_registry.register_tool(add)

    assert first_registry.get_tool("add") is not None

    with pytest.raises(KeyError):
        second_registry.get_tool("add")


def test_decorated_function_remains_callable():
    @tool
    def multiply(a: int, b: int) -> int:
        """Multiply two integers."""
        return a * b

    assert multiply(3, 4) == 12
