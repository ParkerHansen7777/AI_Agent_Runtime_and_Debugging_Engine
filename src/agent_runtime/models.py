import abc

class ModelResponse:
    def __init__(self, res_type: str, content: str = None, tool_name: str = None, arguments: dict = None):
        
        if res_type == "final":
            self.res_type = res_type

            if content is None:
                raise ValueError("content must be provided for final response type")

            self.content = content
            self.tool_name = None
            self.arguments = None

            if tool_name is not None or arguments is not None:
                raise ValueError("tool_name and arguments should not be provided for final response type")

        elif res_type == "tool_call":
            self.res_type = res_type

            if tool_name is None or arguments is None:
                raise ValueError("tool_name and arguments must be provided for tool_call response type")

            self.content = None
            self.tool_name = tool_name
            self.arguments = arguments

            if content is not None:
                raise ValueError("content should not be provided for tool_call response type")

        else:
            raise ValueError("res_type must be either 'final' or 'tool_call'")

class BaseModel(abc.ABC):

    @abc.abstractmethod
    def generate(self, instructions: str, messages: list, tools: list) -> ModelResponse:
        pass

class FakeModel(BaseModel):
    def __init__(self, responses: list):
        if responses is None or not isinstance(responses, list) or not all(isinstance(r, ModelResponse) for r in responses):
            raise ValueError("responses must be a list of ModelResponse objects")
        
        self.responses = responses
        self.current_index = 0
    
    def generate(self, instructions: str, messages: list, tools: list) -> ModelResponse:
        if self.current_index >= len(self.responses):
            raise ValueError("No more responses available in FakeModel.")
        
        res = self.responses[self.current_index]
        self.current_index += 1
        return res