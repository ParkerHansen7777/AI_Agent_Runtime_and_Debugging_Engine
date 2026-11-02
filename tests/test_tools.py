import inspect
import pytest

from agent_runtime.tools import (
    Tool,
    Parameter,
    build_parameters,
    ToolRegistry,
    tool,
)


# --------------------------------------------------
# Test functions
# --------------------------------------------------

@tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


@tool
def search(query: str, limit: int = 10, exact: bool = False):
    """Search for something."""
    return query


# --------------------------------------------------
# Tool tests
# --------------------------------------------------

def test_tool_stores_its_attributes():
    tool_object = Tool(
        name="add",
        description="Add two integers.",
        parameters=add.parameters,
        func=add,
    )

    assert tool_object.name == "add"
    assert tool_object.description == "Add two integers."
    assert tool_object.parameters == add.parameters
    assert tool_object.func is add


def test_tool_callable_executes_original_function():
    assert add(2, 3) == 5


def test_decorated_function_remains_callable():
    @tool
    def multiply(a: int, b: int) -> int:
        """Multiply two integers."""
        return a * b

    assert multiply(3, 4) == 12


# --------------------------------------------------
# Parameter tests
# --------------------------------------------------

def test_parameter_stores_its_attributes():
    parameter = Parameter("limit", int, 10, False)

    assert parameter.name == "limit"
    assert parameter.param_type is int
    assert parameter.default == 10
    assert parameter.required is False


def test_parameter_converts_empty_annotation_to_none():
    parameter = Parameter(
        "query",
        inspect.Parameter.empty,
        inspect.Parameter.empty,
        True,
    )

    assert parameter.param_type is None


def test_build_parameters_extracts_required_parameters():
    parameters = build_parameters(
        inspect.signature(add).parameters
    )

    assert parameters["a"].name == "a"
    assert parameters["a"].param_type is int
    assert parameters["a"].required is True

    assert parameters["b"].name == "b"
    assert parameters["b"].param_type is int
    assert parameters["b"].required is True


def test_build_parameters_extracts_optional_parameters():
    parameters = build_parameters(
        inspect.signature(search).parameters
    )

    assert parameters["limit"].param_type is int
    assert parameters["limit"].default == 10
    assert parameters["limit"].required is False

    assert parameters["exact"].param_type is bool
    assert parameters["exact"].default is False
    assert parameters["exact"].required is False


def test_build_parameters_handles_missing_annotations():
    parameters = build_parameters(
        inspect.signature(search).parameters
    )

    assert parameters["query"].param_type is str


def test_build_parameters_handles_zero_default():
    def example(value: int = 0):
        return value

    parameters = build_parameters(
        inspect.signature(example).parameters
    )

    assert parameters["value"].default == 0
    assert parameters["value"].required is False


def test_build_parameters_handles_empty_string_default():
    def example(value: str = ""):
        return value

    parameters = build_parameters(
        inspect.signature(example).parameters
    )

    assert parameters["value"].default == ""
    assert parameters["value"].required is False


def test_build_parameters_handles_no_parameters():
    def example():
        return "hello"

    parameters = build_parameters(
        inspect.signature(example).parameters
    )

    assert parameters == {}


def test_build_parameters_excludes_return_annotation():
    parameters = build_parameters(
        inspect.signature(add).parameters
    )

    assert "return" not in parameters


def test_build_parameters_handles_unannotated_parameters():
    def example(query):
        return query

    parameters = build_parameters(
        inspect.signature(example).parameters
    )

    assert "query" in parameters
    assert parameters["query"].name == "query"
    assert parameters["query"].param_type is None
    assert parameters["query"].default is inspect.Parameter.empty
    assert parameters["query"].required is True



# --------------------------------------------------
# ToolRegistry tests
# --------------------------------------------------

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

    duplicate_add.name = "add"

    registry.register_tool(add)

    with pytest.raises(ValueError):
        registry.register_tool(duplicate_add)

    assert registry.get_tool("add").func is add


def test_registry_rejects_undecorated_function():
    registry = ToolRegistry()

    def ordinary_function():
        return "hello"

    with pytest.raises(ValueError):
        registry.register_tool(ordinary_function)


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
