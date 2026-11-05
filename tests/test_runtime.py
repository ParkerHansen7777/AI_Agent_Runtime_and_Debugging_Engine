
import pytest

from agent_runtime.agent import Agent
from agent_runtime.models import FakeModel, ModelResponse
from agent_runtime.runtime import Runtime
from agent_runtime.tools import tool


@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers."""
    return a * b


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
