
from copy import deepcopy
from datetime import datetime, timezone

import pytest

from agent_runtime.tracing import ExecutionTrace, TraceEvent


def make_event_dict(event_id="event-1", event_type="tool_execution"):
    return {
        "event_id": event_id,
        "event_type": event_type,
        "timestamp": "2026-11-18T12:00:00+00:00",
        "iteration": 1,
        "duration_ms": 25.5,
        "status": "success",
        "event_details": {
            "tool_name": "search",
            "arguments": {"query": "example"},
        },
    }


def make_trace_dict(status="running", completed_at=None, events=None):
    if events is None:
        events = [make_event_dict()]

    return {
        "schema_version": 1,
        "run_id": "test-run-123",
        "started_at": "2026-11-18T12:00:00+00:00",
        "completed_at": completed_at,
        "status": status,
        "events": events,
    }


# Successful reconstruction

@pytest.mark.parametrize(
    "status, completed_at",
    [
        ("running", None),
        ("completed", "2026-11-18T12:05:00+00:00"),
        ("failed", "2026-11-18T12:05:00+00:00"),
    ],
)
def test_from_dict_reconstructs_valid_trace(status, completed_at):
    data = make_trace_dict(status, completed_at)

    trace = ExecutionTrace.from_dict(data)

    assert trace.run_id == "test-run-123"
    assert trace.started_at == datetime.fromisoformat(data["started_at"])
    assert trace.completed_at == (
        datetime.fromisoformat(completed_at)
        if completed_at is not None
        else None
    )
    assert trace.status == status
    assert len(trace.events) == 1


def test_from_dict_preserves_event_order():
    events = [
        make_event_dict("event-1", "model_call"),
        make_event_dict("event-2", "tool_execution"),
        make_event_dict("event-3", "run_completed"),
    ]

    trace = ExecutionTrace.from_dict(make_trace_dict(events=events))

    assert [event.event_id for event in trace.events] == [
        "event-1",
        "event-2",
        "event-3",
    ]


def test_from_dict_accepts_empty_events_list():
    trace = ExecutionTrace.from_dict(make_trace_dict(events=[]))

    assert trace.events == []


def test_from_dict_preserves_event_details():
    data = make_trace_dict()

    trace = ExecutionTrace.from_dict(data)

    assert trace.events[0].event_details == {
        "tool_name": "search",
        "arguments": {"query": "example"},
    }


def test_from_dict_preserves_timezone_offset():
    data = make_trace_dict()
    data["started_at"] = "2026-11-18T12:00:00-05:00"

    trace = ExecutionTrace.from_dict(data)

    assert trace.started_at.utcoffset().total_seconds() == -18000


# Input validation

def test_from_dict_rejects_non_dictionary():
    with pytest.raises(TypeError):
        ExecutionTrace.from_dict("not a dictionary")


def test_from_dict_rejects_missing_key():
    data = make_trace_dict()
    del data["run_id"]

    with pytest.raises(ValueError):
        ExecutionTrace.from_dict(data)


def test_from_dict_rejects_unexpected_key():
    data = make_trace_dict()
    data["unexpected"] = "value"

    with pytest.raises(ValueError):
        ExecutionTrace.from_dict(data)


# Schema version validation

@pytest.mark.parametrize("version", [True, False, 1.0, "1", None])
def test_from_dict_rejects_invalid_schema_version_type(version):
    data = make_trace_dict()
    data["schema_version"] = version

    with pytest.raises(TypeError):
        ExecutionTrace.from_dict(data)


@pytest.mark.parametrize("version", [0, 2, 3, -1])
def test_from_dict_rejects_unsupported_schema_version(version):
    data = make_trace_dict()
    data["schema_version"] = version

    with pytest.raises(ValueError):
        ExecutionTrace.from_dict(data)


# Field validation

def test_from_dict_rejects_invalid_run_id():
    data = make_trace_dict()
    data["run_id"] = 123

    with pytest.raises(TypeError):
        ExecutionTrace.from_dict(data)


@pytest.mark.parametrize("timestamp", [123, None, True])
def test_from_dict_rejects_invalid_started_at_type(timestamp):
    data = make_trace_dict()
    data["started_at"] = timestamp

    with pytest.raises(TypeError):
        ExecutionTrace.from_dict(data)


def test_from_dict_rejects_invalid_started_at_format():
    data = make_trace_dict()
    data["started_at"] = "not-a-timestamp"

    with pytest.raises(ValueError):
        ExecutionTrace.from_dict(data)


@pytest.mark.parametrize("timestamp", [123, True, ""])
def test_from_dict_rejects_invalid_completed_at(timestamp):
    data = make_trace_dict(
        status="completed",
        completed_at=timestamp,
    )

    with pytest.raises((TypeError, ValueError)):
        ExecutionTrace.from_dict(data)


def test_from_dict_rejects_invalid_status_type():
    data = make_trace_dict()
    data["status"] = 123

    with pytest.raises(TypeError):
        ExecutionTrace.from_dict(data)


def test_from_dict_rejects_unknown_status():
    data = make_trace_dict()
    data["status"] = "pending"

    with pytest.raises(ValueError):
        ExecutionTrace.from_dict(data)


# Status and completion timestamp consistency

def test_from_dict_rejects_running_trace_with_completed_at():
    data = make_trace_dict(
        status="running",
        completed_at="2026-11-18T12:05:00+00:00",
    )

    with pytest.raises(ValueError):
        ExecutionTrace.from_dict(data)


@pytest.mark.parametrize("status", ["completed", "failed"])
def test_from_dict_rejects_finalized_trace_without_completed_at(status):
    data = make_trace_dict(status=status, completed_at=None)

    with pytest.raises(ValueError):
        ExecutionTrace.from_dict(data)


# Event validation

def test_from_dict_rejects_non_list_events():
    data = make_trace_dict()
    data["events"] = "not a list"

    with pytest.raises(TypeError):
        ExecutionTrace.from_dict(data)


def test_from_dict_rejects_invalid_event_type():
    data = make_trace_dict()
    data["events"] = ["not an event dictionary"]

    with pytest.raises(TypeError):
        ExecutionTrace.from_dict(data)


def test_from_dict_rejects_malformed_event():
    data = make_trace_dict()
    del data["events"][0]["event_id"]

    with pytest.raises(ValueError):
        ExecutionTrace.from_dict(data)


# Input immutability

def test_from_dict_does_not_modify_original_data():
    data = make_trace_dict()
    original_data = deepcopy(data)

    ExecutionTrace.from_dict(data)

    assert data == original_data


# Serialization / deserialization round trip

def test_to_dict_and_from_dict_round_trip():
    started_at = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)

    trace = ExecutionTrace("test-run-123", started_at)

    event = TraceEvent(
        event_id="event-1",
        event_type="tool_execution",
        timestamp=started_at,
        iteration=1,
        duration_ms=25.5,
        status="success",
        event_details={"tool_name": "search"},
    )

    trace.add_event(event)
    trace.finish("completed")

    serialized = trace.to_dict()
    reconstructed = ExecutionTrace.from_dict(serialized)

    assert reconstructed.to_dict() == serialized
