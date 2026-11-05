
import pytest

from agent_runtime.tools import Tool, tool


@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers."""
    return a * b


@tool
def greet(name: str, greeting: str = "Hello") -> str:
    """Greet someone."""
    return f"{greeting}, {name}!"


@tool
def flexible(value):
    """Accept a value of any type."""
    return value


def create_tool(func):
    return Tool(
        name=func.name,
        description=func.description,
        parameters=func.parameters,
        func=func
    )


def test_valid_arguments_are_accepted():
    tool_instance = create_tool(multiply)

    tool_instance.validate_arguments({"a": 5, "b": 10})


def test_missing_required_argument_raises_value_error():
    tool_instance = create_tool(multiply)

    with pytest.raises(ValueError, match="Missing required argument"):
        tool_instance.validate_arguments({"a": 5})


def test_all_missing_required_arguments_are_detected():
    tool_instance = create_tool(multiply)

    with pytest.raises(ValueError, match="Missing required argument"):
        tool_instance.validate_arguments({})


def test_unexpected_argument_raises_value_error():
    tool_instance = create_tool(multiply)

    with pytest.raises(ValueError, match="Unexpected argument"):
        tool_instance.validate_arguments({"a": 5, "b": 10, "c": 15})


def test_incorrect_argument_type_raises_type_error():
    tool_instance = create_tool(multiply)

    with pytest.raises(TypeError, match="must be of type int"):
        tool_instance.validate_arguments({"a": "5", "b": 10})


def test_boolean_true_rejected_for_integer_parameter():
    tool_instance = create_tool(multiply)

    with pytest.raises(TypeError, match="must be of type int"):
        tool_instance.validate_arguments({"a": True, "b": 10})


def test_boolean_false_rejected_for_integer_parameter():
    tool_instance = create_tool(multiply)

    with pytest.raises(TypeError, match="must be of type int"):
        tool_instance.validate_arguments({"a": False, "b": 10})


def test_unannotated_parameter_accepts_any_type():
    tool_instance = create_tool(flexible)

    tool_instance.validate_arguments({"value": "hello"})
    tool_instance.validate_arguments({"value": 123})
    tool_instance.validate_arguments({"value": None})


def test_optional_parameter_can_be_omitted():
    tool_instance = create_tool(greet)

    tool_instance.validate_arguments({"name": "Alice"})


def test_optional_parameter_accepts_correct_type():
    tool_instance = create_tool(greet)

    tool_instance.validate_arguments({
        "name": "Alice",
        "greeting": "Good morning"
    })


def test_optional_parameter_rejects_incorrect_type():
    tool_instance = create_tool(greet)

    with pytest.raises(TypeError, match="must be of type str"):
        tool_instance.validate_arguments({
            "name": "Alice",
            "greeting": 123
        })


@pytest.mark.parametrize("invalid_args", [
    None,
    "hello",
    [1, 2, 3],
    123,
    True
])
def test_non_dictionary_arguments_raise_type_error(invalid_args):
    tool_instance = create_tool(multiply)

    with pytest.raises(TypeError, match="dictionary"):
        tool_instance.validate_arguments(invalid_args)


def test_none_is_rejected_for_required_integer_parameter():
    tool_instance = create_tool(multiply)

    with pytest.raises(TypeError, match="must be of type int"):
        tool_instance.validate_arguments({"a": None, "b": 10})
