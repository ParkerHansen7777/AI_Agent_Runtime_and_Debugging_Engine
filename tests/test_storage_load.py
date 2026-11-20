
import json
from datetime import datetime, timezone

import pytest

from agent_runtime.storage import TraceStorage
from agent_runtime.tracing import ExecutionTrace, TraceEvent


def make_trace(run_id="run-123", events=None):
    trace = ExecutionTrace(
        run_id=run_id,
        started_at=datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc),
    )

    if events:
        trace.events = events

    return trace


def make_event(event_id="event-1"):
    return TraceEvent(
        event_id=event_id,
        event_type="tool_execution",
        timestamp=datetime(2026, 11, 19, 12, 1, tzinfo=timezone.utc),
        iteration=1,
        duration_ms=25.5,
        status="success",
        event_details={"tool_name": "calculator", "result": 42},
    )


# Successful loading

def test_load_returns_execution_trace(tmp_path):
    storage = TraceStorage(tmp_path)
    original = make_trace()

    storage.save(original)
    loaded = storage.load("run-123")

    assert isinstance(loaded, ExecutionTrace)


def test_load_reconstructs_original_trace(tmp_path):
    storage = TraceStorage(tmp_path)
    original = make_trace(events=[make_event()])

    storage.save(original)
    loaded = storage.load("run-123")

    assert loaded.to_dict() == original.to_dict()


def test_load_preserves_event_order(tmp_path):
    storage = TraceStorage(tmp_path)
    original = make_trace(
        events=[
            make_event("event-1"),
            make_event("event-2"),
            make_event("event-3"),
        ]
    )

    storage.save(original)
    loaded = storage.load("run-123")

    assert [event.event_id for event in loaded.events] == [
        "event-1",
        "event-2",
        "event-3",
    ]


def test_load_preserves_event_details(tmp_path):
    storage = TraceStorage(tmp_path)
    original = make_trace(events=[make_event()])

    storage.save(original)
    loaded = storage.load("run-123")

    assert loaded.events[0].event_details == {
        "tool_name": "calculator",
        "result": 42,
    }


def test_load_trace_with_no_events(tmp_path):
    storage = TraceStorage(tmp_path)
    original = make_trace()

    storage.save(original)
    loaded = storage.load("run-123")

    assert loaded.events == []


def test_load_trace_with_none_completed_at(tmp_path):
    storage = TraceStorage(tmp_path)
    original = make_trace()

    storage.save(original)
    loaded = storage.load("run-123")

    assert loaded.completed_at is None


# Run ID validation

@pytest.mark.parametrize("run_id", [123, None, [], {}])
def test_load_rejects_non_string_run_id(tmp_path, run_id):
    storage = TraceStorage(tmp_path)

    with pytest.raises(TypeError):
        storage.load(run_id)


@pytest.mark.parametrize(
    "run_id",
    [
        "",
        "../outside",
        "run/123",
        "run\\123",
        "run.123",
    ],
)
def test_load_rejects_invalid_run_id(tmp_path, run_id):
    storage = TraceStorage(tmp_path)

    with pytest.raises(ValueError):
        storage.load(run_id)


# File errors

def test_load_missing_file_raises_file_not_found_error(tmp_path):
    storage = TraceStorage(tmp_path)

    with pytest.raises(FileNotFoundError):
        storage.load("missing-run")


def test_load_malformed_json_raises_json_decode_error(tmp_path):
    storage = TraceStorage(tmp_path)
    filepath = tmp_path / "run-123.json"
    filepath.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        storage.load("run-123")


# Deserialization errors

def test_load_invalid_trace_structure_raises_error(tmp_path):
    storage = TraceStorage(tmp_path)
    filepath = tmp_path / "run-123.json"

    filepath.write_text(
        json.dumps({"invalid": "trace"}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        storage.load("run-123")


def test_load_unsupported_schema_version_raises_value_error(tmp_path):
    storage = TraceStorage(tmp_path)
    original = make_trace()
    data = original.to_dict()
    data["schema_version"] = 999

    filepath = tmp_path / "run-123.json"
    filepath.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError):
        storage.load("run-123")
