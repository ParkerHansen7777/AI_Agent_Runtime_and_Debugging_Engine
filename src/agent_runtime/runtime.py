from agent_runtime.agent import Agent
from agent_runtime.models import BaseModel

class Runtime:
    def __init__(self, agent: 'Agent', model: 'BaseModel', max_iterations: int = 10):
        self.agent = agent
        self.model = model
        self.max_iterations = max_iterations
    
    def run(self, user_input: str):
        messages = [{"role": "user", "content": user_input}]
        iterations = 0
        tool_calls = []

        while iterations < self.max_iterations:
        
            response = self.model.generate(self.agent.instructions, messages, self.agent.registry.list_tool_schemas())
            iterations += 1

            if response.res_type == "final":
                messages.append({"role": "assistant", "content": response.content})
                return RunResult(output=response.content, messages=messages, iterations=iterations, tool_calls=tool_calls)
            
            elif response.res_type == "tool_call":
                tool = self.agent.registry.get_tool(response.tool_name)
                messages.append({"role": "assistant", "content": None, "tool_call": {"tool_name": response.tool_name, "arguments": response.arguments}})

                tool.validate_arguments(response.arguments)
                result = tool.func(**response.arguments)
                messages.append({"role": "tool", "name": response.tool_name, "content": result})
                tool_calls.append({"tool_name": response.tool_name, "arguments": response.arguments, "result": result, "success": True})
        raise RuntimeError(f"Maximum iterations of {self.max_iterations} exceeded without reaching a final response.")


class RunResult:
    def __init__(self, output: str, messages: list, iterations: int, tool_calls: list):
        self.output = output
        self.messages = messages.copy()
        self.iterations = iterations
        self.tool_calls = tool_calls.copy()