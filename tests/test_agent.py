import pytest

from agent_runtime.agent import Agent
from agent_runtime.tools import Tool, tool


# --------------------------------------------------
# Test functions
# --------------------------------------------------

@tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


# --------------------------------------------------
# Agent initialization tests
# --------------------------------------------------

def test_agent_stores_name_and_instructions():
    agent = Agent(
        name="Math Agent",
        instructions="You are a helpful math assistant.",
    )

    assert agent.name == "Math Agent"
    assert agent.instructions == "You are a helpful math assistant."


def test_agent_creates_its_own_registry():
    agent = Agent(
        name="Math Agent",
        instructions="You are a helpful math assistant.",
    )

    assert agent.registry is not None


def test_each_agent_has_an_independent_registry():
    first_agent = Agent("First Agent", "First instructions.")
    second_agent = Agent("Second Agent", "Second instructions.")

    assert first_agent.registry is not second_agent.registry


# --------------------------------------------------
# Tool registration tests
# --------------------------------------------------

def test_agent_registers_tool():
    agent = Agent("Math Agent", "You are a math assistant.")

    agent.register_tool(add)

    registered_tool = agent.registry.get_tool("add")

    assert isinstance(registered_tool, Tool)
    assert registered_tool.name == "add"
    assert registered_tool.func is add


def test_agent_register_tool_returns_original_function():
    agent = Agent("Math Agent", "You are a math assistant.")

    result = agent.register_tool(add)

    assert result is add


def test_agent_can_register_multiple_tools():
    agent = Agent("Math Agent", "You are a math assistant.")

    @tool
    def subtract(a: int, b: int) -> int:
        """Subtract two integers."""
        return a - b

    agent.register_tool(add)
    agent.register_tool(subtract)

    assert set(agent.registry.list_tools()) == {"add", "subtract"}


def test_registering_tool_does_not_affect_another_agent():
    first_agent = Agent("First Agent", "First instructions.")
    second_agent = Agent("Second Agent", "Second instructions.")

    first_agent.register_tool(add)

    assert "add" in first_agent.registry.list_tools()
    assert "add" not in second_agent.registry.list_tools()


def test_agent_rejects_undecorated_function():
    agent = Agent("Math Agent", "You are a math assistant.")

    def ordinary_function():
        return "hello"

    with pytest.raises(ValueError):
        agent.register_tool(ordinary_function)
