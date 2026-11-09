
import pytest

from agent_runtime.agent import Agent
from agent_runtime.models import FakeModel, ModelResponse
from agent_runtime.runtime import Runtime
from agent_runtime.tools import tool


tool_execution_count = 0

class SchemaCaptureModel:
    def __init__(self):
        self.received_tools = None

    def generate(self, instructions, messages, tools):
        self.received_tools = tools
        return ModelResponse(
            res_type="final",
            content="Finished."
        )


@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers."""
    global tool_execution_count
    tool_execution_count += 1
    return a * b


def create_runtime(arguments):
    agent = Agent("Math Agent", "You are a math assistant.")
    agent.register_tool(multiply)

    model = FakeModel(responses=[
        ModelResponse(
            res_type="tool_call",
            tool_name="multiply",
            arguments=arguments
        )
    ])

    return Runtime(agent, model)


def test_runtime_returns_immediate_final_response():
    agent = Agent("Math Agent", "You are a math assistant.")

    model = FakeModel(responses=[
        ModelResponse(
            res_type="final",
            content="Hello! How can I help you?"
        )
    ])

    runtime = Runtime(agent, model)

    result = runtime.run("Hello!")

    assert result.output == "Hello! How can I help you?"
    assert result.iterations == 1
    assert result.tool_calls == []
    assert result.messages == [
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hello! How can I help you?"}
    ]


def test_runtime_executes_tool_then_returns_final_response():
    agent = Agent("Math Agent", "You are a math assistant.")
    agent.register_tool(multiply)

    model = FakeModel(responses=[
        ModelResponse(
            res_type="tool_call",
            tool_name="multiply",
            arguments={"a": 15, "b": 8}
        ),
        ModelResponse(
            res_type="final",
            content="15 multiplied by 8 is 120."
        )
    ])

    runtime = Runtime(agent, model)

    result = runtime.run("What is 15 multiplied by 8?")

    assert result.output == "15 multiplied by 8 is 120."
    assert result.iterations == 2

    assert len(result.tool_calls) == 1
    assert result.tool_calls[0] == {
        "tool_name": "multiply",
        "arguments": {"a": 15, "b": 8},
        "result": 120,
        "success": True
    }

    assert result.messages == [
        {"role": "user", "content": "What is 15 multiplied by 8?"},
        {
            "role": "assistant",
            "content": None,
            "tool_call": {
                "tool_name": "multiply",
                "arguments": {"a": 15, "b": 8}
            }
        },
        {"role": "tool", "name": "multiply", "content": 120},
        {
            "role": "assistant",
            "content": "15 multiplied by 8 is 120."
        }
    ]

    assert model.current_index == 2


def test_runtime_raises_error_when_max_iterations_exceeded():
    agent = Agent("Math Agent", "You are a math assistant.")
    agent.register_tool(multiply)

    model = FakeModel(responses=[
        ModelResponse(
            res_type="tool_call",
            tool_name="multiply",
            arguments={"a": 2, "b": 3}
        ),
        ModelResponse(
            res_type="tool_call",
            tool_name="multiply",
            arguments={"a": 4, "b": 5}
        )
    ])

    runtime = Runtime(agent, model, max_iterations=2)

    with pytest.raises(RuntimeError, match="Maximum iterations"):
        runtime.run("Perform some multiplication.")

    assert model.current_index == 2


# Argument validation integration tests


def test_runtime_accepts_valid_tool_arguments():
    global tool_execution_count
    tool_execution_count = 0

    runtime = create_runtime({"a": 5, "b": 10})

    with pytest.raises(ValueError, match="No more responses"):
        runtime.run("Multiply 5 by 10.")

    assert tool_execution_count == 1


def test_runtime_rejects_missing_required_arguments():
    global tool_execution_count
    tool_execution_count = 0

    runtime = create_runtime({"a": 5})

    with pytest.raises(ValueError, match="Missing required argument"):
        runtime.run("Multiply 5 by something.")

    assert tool_execution_count == 0


def test_runtime_rejects_unexpected_arguments():
    global tool_execution_count
    tool_execution_count = 0

    runtime = create_runtime({"a": 5, "b": 10, "c": 15})

    with pytest.raises(ValueError, match="Unexpected argument"):
        runtime.run("Multiply some numbers.")

    assert tool_execution_count == 0


def test_runtime_rejects_incorrect_argument_types():
    global tool_execution_count
    tool_execution_count = 0

    runtime = create_runtime({"a": "five", "b": 10})

    with pytest.raises(TypeError, match="must be of type int"):
        runtime.run("Multiply some numbers.")

    assert tool_execution_count == 0


def test_runtime_rejects_boolean_for_integer_argument():
    global tool_execution_count
    tool_execution_count = 0

    runtime = create_runtime({"a": True, "b": 10})

    with pytest.raises(TypeError, match="must be of type int"):
        runtime.run("Multiply some numbers.")

    assert tool_execution_count == 0


def test_runtime_records_tool_call_before_validation_fails():
    runtime = create_runtime({"a": 5})

    with pytest.raises(ValueError, match="Missing required argument"):
        runtime.run("Multiply some numbers.")

def test_runtime_passes_tool_schemas_to_model():
    @tool
    def multiply(a: int, b: int):
        """Multiply two integers."""

    agent = Agent("Test Agent", "You are a test agent.")
    agent.register_tool(multiply)

    model = SchemaCaptureModel()
    runtime = Runtime(agent, model)

    runtime.run("Multiply 5 and 10.")

    assert model.received_tools == [
        {
            "name": "multiply",
            "description": "Multiply two integers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"},
                },
                "required": ["a", "b"],
                "additionalProperties": False,
            },
        }
    ]


def test_runtime_passes_empty_schema_list_when_no_tools_registered():
    agent = Agent("Test Agent", "You are a test agent.")

    model = SchemaCaptureModel()
    runtime = Runtime(agent, model)

    runtime.run("Hello.")

    assert model.received_tools == []
