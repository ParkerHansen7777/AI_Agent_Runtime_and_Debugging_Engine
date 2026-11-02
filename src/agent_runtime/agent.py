from agent_runtime.tools import ToolRegistry


class Agent:
    def __init__(self, name: str, instructions: str):
        self.name = name
        self.instructions = instructions
        self.registry = ToolRegistry()

    def register_tool(self, func: callable):
        self.registry.register_tool(func)
        return func