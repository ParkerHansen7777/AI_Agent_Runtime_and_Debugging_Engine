class Tool:
    def __init__(self, name: str, description: str, parameters: dict, func: callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func

def tool(func: callable):
    func.name = func.__name__
    func.description = func.__doc__ or ""
    func.parameters = func.__annotations__

    return func

class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register_tool(self, func: callable):
        if not func.name:
            raise ValueError("function not decorated with @tool")
        
        if func.name in self.tools:
            raise ValueError(f"Tool with name '{func.name}' is already registered.")
         
        self.tools[func.name] = Tool(func.name, func.description, func.parameters, func)

    def get_tool(self, name: str) -> Tool:
        if name not in self.tools:
            raise KeyError(f"Tool with name '{name}' is not registered.")
        return self.tools[name]

    def list_tools(self):
        return list(self.tools.keys())
