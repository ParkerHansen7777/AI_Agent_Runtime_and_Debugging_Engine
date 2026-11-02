import inspect


class Tool:
    def __init__(self, name: str, description: str, parameters: dict, func: callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func

class Parameter:
    def __init__(self, name: str, param_type: type, default=None, required=True):
        self.name = name
        self.param_type = None if param_type is inspect.Parameter.empty else param_type
        self.default = default
        self.required = required

def build_parameters(params: dict) -> dict:
    parameters = {}
    for name, param in params.items():
        parameters[name] = Parameter(name, param.annotation, param.default, param.default == inspect.Parameter.empty)
    return parameters

def tool(func: callable):
    func.name = func.__name__
    func.description = func.__doc__ or ""


    func.parameters = build_parameters(inspect.signature(func).parameters)

    return func

class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register_tool(self, func: callable):
        if not (hasattr(func, 'name') and hasattr(func, 'description') and hasattr(func, 'parameters')):
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
