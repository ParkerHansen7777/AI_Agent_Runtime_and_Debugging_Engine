import inspect


class Tool:
    def __init__(self, name: str, description: str, parameters: dict, func: callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func

    def to_schema(self):
        
        type_schema_mapping = {
            int: "integer",
            float: "number",
            str: "string",
            bool: "boolean",
        }
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    param.name: {
                        **({"type": type_schema_mapping[param.param_type]} if param.param_type in type_schema_mapping else {})
                    }
                    for param in self.parameters.values()
                },
                "required": [param.name for param in self.parameters.values() if param.required],
                "additionalProperties": False  
            },
             
        }

    def validate_arguments(self, args: dict):

        if not isinstance(args, dict):
            raise TypeError("Arguments must be provided as a dictionary.")
        
        for param_name, param in self.parameters.items():
            
            if param.required and param_name not in args:
                raise ValueError(f"Missing required argument: {param_name}")
            
            if param_name in args and isinstance(args[param_name], bool) and param.param_type is int:
                raise TypeError(f"Argument '{param_name}' must be of type int")
            
            if param_name in args and param.param_type is not None and not isinstance(args[param_name], param.param_type):
                raise TypeError(f"Argument '{param_name}' must be of type {param.param_type.__name__}")

        for arg_name in args:
            if arg_name not in self.parameters:
                raise ValueError(f"Unexpected argument: {arg_name}")
            

            

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

    def list_tool_schemas(self):
        return [tool.to_schema() for tool in self.tools.values()]
