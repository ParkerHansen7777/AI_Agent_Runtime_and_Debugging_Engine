from datetime import datetime, timezone
from time import perf_counter

from agent_runtime.agent import Agent
from agent_runtime.models import BaseModel
from agent_runtime.tracing import ExecutionTrace
import uuid

class Runtime:
    def __init__(self, agent: 'Agent', model: 'BaseModel', max_iterations: int = 10):
        self.agent = agent
        self.model = model
        self.max_iterations = max_iterations
    
    def run(self, user_input: str):
        messages = [{"role": "user", "content": user_input}]
        iterations = 0
        tool_calls = []
        started_at = datetime.now(timezone.utc)
        run_start = perf_counter()
        trace = ExecutionTrace(run_id=str(uuid.uuid4()), started_at=started_at)
        trace.record_event(event_type="run_started", status="info", event_details={"user_input": user_input, "max_iterations": self.max_iterations})
        
        try:

            while iterations < self.max_iterations:
            
                call_start = perf_counter()
                try:
                    response = self.model.generate(self.agent.instructions, messages, self.agent.registry.list_tool_schemas())
                except Exception as exe:
                    trace.record_event(event_type="model_error", iteration=iterations + 1, duration_ms=(perf_counter() - call_start) * 1000, status="error", event_details={"error_type": type(exe).__name__, "error_message": str(exe)})
                    raise
                
                duration_ms = (perf_counter() - call_start) * 1000
                trace.record_event(event_type="model_call", iteration=iterations + 1, duration_ms=duration_ms, status="success", event_details={"response_type": response.res_type})
                iterations += 1

                if response.res_type == "final":
                    messages.append({"role": "assistant", "content": response.content})
                    total_duration_ms = (perf_counter() - run_start) * 1000
                    trace.record_event(event_type="run_completed", iteration=iterations, duration_ms=total_duration_ms, event_details={"output": response.content})
                    trace.finish("completed") 
                    return RunResult(output=response.content, messages=messages, iterations=iterations, tool_calls=tool_calls, trace=trace)
                
                elif response.res_type == "tool_call":
                    
                    tool_start = perf_counter()
                    try:
                        tool = self.agent.registry.get_tool(response.tool_name)
                        messages.append({"role": "assistant", "content": None, "tool_call": {"tool_name": response.tool_name, "arguments": response.arguments}})

                        tool.validate_arguments(response.arguments)
                        result = tool.func(**response.arguments)
                        messages.append({"role": "tool", "name": response.tool_name, "content": result})
                    except Exception as exe:
                        trace.record_event(event_type="tool_error", iteration=iterations, duration_ms=(perf_counter() - tool_start) * 1000, status="error", event_details={"tool_name": response.tool_name, "error_type": type(exe).__name__, "error_message": str(exe), "arguments": response.arguments})
                        raise 
                    
                    duration_ms = (perf_counter() - tool_start) * 1000
                    trace.record_event(event_type="tool_execution", iteration=iterations, duration_ms=duration_ms, status="success", event_details={"tool_name": response.tool_name, "arguments": response.arguments, "result": result})
                    tool_calls.append({"tool_name": response.tool_name, "arguments": response.arguments, "result": result, "success": True})
            
            raise RuntimeError(f"Maximum iterations of {self.max_iterations} exceeded without reaching a final response.")

        except Exception as exe:
            trace.record_event(event_type="run_failed", iteration=iterations, duration_ms=(perf_counter() - run_start) * 1000, status="error", event_details={"error_type": type(exe).__name__, "error_message": str(exe)})
            trace.finish("failed")
            exe.trace = trace
            raise


class RunResult:
    def __init__(self, output: str, messages: list, iterations: int, tool_calls: list, trace: ExecutionTrace):
        self.output = output
        self.messages = messages.copy()
        self.iterations = iterations
        self.tool_calls = tool_calls.copy()
        self.trace = trace