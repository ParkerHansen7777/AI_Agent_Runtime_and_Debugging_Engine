# AI_Agent_Runtime_and_Debugging_Engine

A Python runtime for executing, tracing, and debugging AI agents.

## Project goals

- Execute multi-step AI agent workflows.
- Support explicitly registered tools through a `@tool` decorator.
- Enforce execution limits and handle failures.
- Record execution traces for debugging.
- Evaluate agent reliability, latency, and cost.

## Development

Requires Python 3.11 or newer.

Create and activate a virtual environment, then install the development dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Run tests:

```powershell
pytest
```

