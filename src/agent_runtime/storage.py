from agent_runtime.tracing import ExecutionTrace 
from pathlib import Path
import json
import re

class TraceStorage():

    def __init__(self, directory):
        if not isinstance(directory, (str, Path)):
            raise TypeError("Invalid type for directory path, must be either a string or Path")

        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, trace: ExecutionTrace):
        if not isinstance(trace, ExecutionTrace):
            raise TypeError("trace is not type ExecutionTrace")

        if not isinstance(trace.run_id, str):
            raise TypeError("run_id must be string")
        
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", trace.run_id):
            raise ValueError("run_id must not be empty and contain only letters, numbers, hyphens and underscores, no path separators allowed")

        filepath = self.directory / f"{trace.run_id}.json"
        data = json.dumps(trace.to_dict(), indent=2, allow_nan=False)

        with open(filepath, "x", encoding="utf-8") as file:
            file.write(data)

        return filepath

    def load(self, run_id):
        if not isinstance(run_id, str):
            raise TypeError("run_id must be a string")

        if not re.fullmatch(r"[a-zA-Z0-9_-]+", run_id):
            raise ValueError("run_id must not be empty and contain only letters, numbers, hyphens and underscores, no path separators allowed")

        filepath = self.directory / f"{run_id}.json"

        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)

        return ExecutionTrace.from_dict(data)

    def list_traces(self):
        res = []
        for file in self.directory.iterdir():
            if file.is_file() and file.suffix == ".json":
                res.append(file.stem)
        return sorted(res)