
import pytest
import json
import math
from datetime import datetime, timezone

from agent_runtime.tracing import TraceEvent, ExecutionTrace


@pytest.fixture
def sample_timestamp():
    return datetime(2026, 11, 12, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def sample_event(sample_timestamp):
    return TraceEvent(
        event_id="event-123",
        event_type="tool_execution",
        timestamp=sample_timestamp,
        iteration=2,
        duration_ms=125.5,
        status="success",
        event_details={"tool_name": "calculator", "result": 42}
    )


@pytest.fixture
def trace_event():
    return TraceEvent(
        event_id="event-1",
        event_type="model_call",
        timestamp=datetime.now(timezone.utc),
        iteration=1,
        duration_ms=125.5,
        status="success",
        event_details={"response_type": "tool_call"}
    )


@pytest.fixture
def execution_trace():
    return ExecutionTrace(
        run_id="run-1",
        started_at=datetime.now(timezone.utc)
    )


# -------------------------
# TraceEvent tests
# -------------------------

def test_trace_event_initialization():
    timestamp = datetime.now(timezone.utc)

    event = TraceEvent(
        event_id="event-1",
        event_type="model_call",
        timestamp=timestamp,
        iteration=1,
        duration_ms=125.5,
        status="success",
        event_details={"response_type": "final"}
    )

    assert event.event_id == "event-1"
    assert event.event_type == "model_call"
    assert event.timestamp == timestamp
    assert event.iteration == 1
    assert event.duration_ms == 125.5
    assert event.status == "success"
    assert event.event_details == {"response_type": "final"}


def test_trace_event_default_values():
    event = TraceEvent(
        event_id="event-1",
        event_type="run_started",
        timestamp=datetime.now(timezone.utc)
    )

    assert event.iteration is None
    assert event.duration_ms is None
    assert event.status == "info"
    assert event.event_details == {}


# -------------------------
# ExecutionTrace initialization
# -------------------------

def test_execution_trace_initialization(execution_trace):
    assert execution_trace.run_id == "run-1"
    assert execution_trace.status == "running"
    assert execution_trace.completed_at is None
    assert execution_trace.events == []


def test_execution_trace_copies_initial_events(trace_event):
    original_events = [trace_event]

    trace = ExecutionTrace(
        run_id="run-1",
        started_at=datetime.now(timezone.utc),
        events=original_events
    )

    original_events.clear()

    assert len(trace.events) == 1


# -------------------------
# add_event tests
# -------------------------

def test_add_event(execution_trace, trace_event):
    execution_trace.add_event(trace_event)

    assert len(execution_trace.events) == 1
    assert execution_trace.events[0] is trace_event


def test_add_invalid_event(execution_trace):
    with pytest.raises(TypeError):
        execution_trace.add_event("not a TraceEvent")


@pytest.mark.parametrize("final_status", ["completed", "failed"])
def test_add_event_after_finalization(final_status, execution_trace, trace_event):
    execution_trace.finish(final_status)

    with pytest.raises(RuntimeError):
        execution_trace.add_event(trace_event)


# -------------------------
# get_events tests
# -------------------------

def test_get_all_events(execution_trace):
    event1 = TraceEvent(
        "event-1", "model_call", datetime.now(timezone.utc)
    )
    event2 = TraceEvent(
        "event-2", "tool_execution", datetime.now(timezone.utc)
    )

    execution_trace.add_event(event1)
    execution_trace.add_event(event2)

    events = execution_trace.get_events()

    assert events == [event1, event2]


def test_get_events_by_type(execution_trace):
    event1 = TraceEvent(
        "event-1", "model_call", datetime.now(timezone.utc)
    )
    event2 = TraceEvent(
        "event-2", "tool_execution", datetime.now(timezone.utc)
    )
    event3 = TraceEvent(
        "event-3", "model_call", datetime.now(timezone.utc)
    )

    execution_trace.add_event(event1)
    execution_trace.add_event(event2)
    execution_trace.add_event(event3)

    events = execution_trace.get_events("model_call")

    assert events == [event1, event3]


def test_get_events_returns_copy(execution_trace, trace_event):
    execution_trace.add_event(trace_event)

    events = execution_trace.get_events()
    events.clear()

    assert len(execution_trace.events) == 1


def test_get_events_unknown_type(execution_trace, trace_event):
    execution_trace.add_event(trace_event)

    assert execution_trace.get_events("unknown_event") == []


# -------------------------
# finish tests
# -------------------------

def test_finish_completed(execution_trace):
    execution_trace.finish("completed")

    assert execution_trace.status == "completed"
    assert isinstance(execution_trace.completed_at, datetime)
    assert execution_trace.completed_at.tzinfo == timezone.utc


def test_finish_failed(execution_trace):
    execution_trace.finish("failed")

    assert execution_trace.status == "failed"
    assert isinstance(execution_trace.completed_at, datetime)
    assert execution_trace.completed_at.tzinfo == timezone.utc


def test_finish_invalid_status(execution_trace):
    with pytest.raises(ValueError):
        execution_trace.finish("running")

    assert execution_trace.status == "running"
    assert execution_trace.completed_at is None


@pytest.mark.parametrize("final_status", ["completed", "failed"])
def test_finish_twice(final_status, execution_trace):
    execution_trace.finish(final_status)

    with pytest.raises(RuntimeError):
        execution_trace.finish("completed")


from datetime import datetime, timezone
from agent_runtime.tracing import ExecutionTrace, TraceEvent


def test_record_event_returns_trace_event():
    trace = ExecutionTrace("run-1", datetime.now(timezone.utc))

    event = trace.record_event("model_call")

    assert isinstance(event, TraceEvent)


def test_record_event_generates_string_event_id():
    trace = ExecutionTrace("run-1", datetime.now(timezone.utc))

    event = trace.record_event("model_call")

    assert isinstance(event.event_id, str)
    assert len(event.event_id) > 0


def test_record_event_generates_unique_ids():
    trace = ExecutionTrace("run-1", datetime.now(timezone.utc))

    event1 = trace.record_event("model_call")
    event2 = trace.record_event("tool_execution")

    assert event1.event_id != event2.event_id


def test_record_event_generates_utc_timestamp():
    trace = ExecutionTrace("run-1", datetime.now(timezone.utc))

    event = trace.record_event("model_call")

    assert isinstance(event.timestamp, datetime)
    assert event.timestamp.tzinfo is not None
    assert event.timestamp.utcoffset().total_seconds() == 0


def test_record_event_adds_event_to_trace():
    trace = ExecutionTrace("run-1", datetime.now(timezone.utc))

    event = trace.record_event("model_call")

    assert event in trace.events
    assert len(trace.events) == 1


def test_record_event_stores_provided_arguments():
    trace = ExecutionTrace("run-1", datetime.now(timezone.utc))
    details = {"model": "fake-model", "response_type": "tool_call"}

    event = trace.record_event(
        event_type="model_call",
        iteration=2,
        duration_ms=125.5,
        status="success",
        event_details=details
    )

    assert event.event_type == "model_call"
    assert event.iteration == 2
    assert event.duration_ms == 125.5
    assert event.status == "success"
    assert event.event_details == details


def test_record_event_uses_default_values():
    trace = ExecutionTrace("run-1", datetime.now(timezone.utc))

    event = trace.record_event("run_started")

    assert event.iteration is None
    assert event.duration_ms is None
    assert event.status == "info"
    assert event.event_details == {}


def test_record_event_rejects_completed_trace():
    trace = ExecutionTrace("run-1", datetime.now(timezone.utc))
    trace.finish("completed")

    with pytest.raises(RuntimeError):
        trace.record_event("model_call")


def test_record_event_rejects_failed_trace():
    trace = ExecutionTrace("run-1", datetime.now(timezone.utc))
    trace.finish("failed")

    with pytest.raises(RuntimeError):
        trace.record_event("model_call")

def test_trace_event_to_dict_serializes_all_fields(sample_event, sample_timestamp):
    result = sample_event.to_dict()

    assert result == {
        "event_id": "event-123",
        "event_type": "tool_execution",
        "timestamp": sample_timestamp.isoformat(),
        "iteration": 2,
        "duration_ms": 125.5,
        "status": "success",
        "event_details": {
            "tool_name": "calculator",
            "result": 42
        }
    }


def test_trace_event_to_dict_preserves_none_values(sample_timestamp):
    event = TraceEvent(
        event_id="event-123",
        event_type="model_call",
        timestamp=sample_timestamp
    )

    result = event.to_dict()

    assert result["iteration"] is None
    assert result["duration_ms"] is None


def test_trace_event_serializes_nested_values(sample_timestamp):
    nested_datetime = datetime(2026, 11, 12, tzinfo=timezone.utc)

    event = TraceEvent(
        event_id="event-123",
        event_type="test",
        timestamp=sample_timestamp,
        event_details={
            "nested": {
                "items": [1, 2, {"timestamp": nested_datetime}]
            }
        }
    )

    result = event.to_dict()

    assert result["event_details"]["nested"]["items"][2]["timestamp"] == nested_datetime.isoformat()


def test_trace_event_rejects_unsupported_values(sample_timestamp):
    event = TraceEvent(
        event_id="event-123",
        event_type="test",
        timestamp=sample_timestamp,
        event_details={"invalid": object()}
    )

    with pytest.raises(TypeError):
        event.to_dict()


def test_trace_event_rejects_non_string_dictionary_keys(sample_timestamp):
    event = TraceEvent(
        event_id="event-123",
        event_type="test",
        timestamp=sample_timestamp,
        event_details={123: "invalid"}
    )

    with pytest.raises(TypeError):
        event.to_dict()


@pytest.mark.parametrize("invalid_float", [float("nan"), float("inf"), float("-inf")])
def test_trace_event_rejects_non_finite_floats(sample_timestamp, invalid_float):
    event = TraceEvent(
        event_id="event-123",
        event_type="test",
        timestamp=sample_timestamp,
        event_details={"value": invalid_float}
    )

    with pytest.raises(ValueError):
        event.to_dict()


def test_trace_event_rejects_non_finite_duration(sample_timestamp):
    event = TraceEvent(
        event_id="event-123",
        event_type="test",
        timestamp=sample_timestamp,
        duration_ms=float("nan")
    )

    with pytest.raises(ValueError):
        event.to_dict()


def test_trace_event_to_dict_does_not_modify_original(sample_event):
    original_details = {
        "tool_name": "calculator",
        "result": 42
    }

    sample_event.to_dict()

    assert sample_event.event_details == original_details
    assert isinstance(sample_event.timestamp, datetime)

def test_execution_trace_to_dict_serializes_metadata(sample_timestamp):
    trace = ExecutionTrace(
        run_id="run-123",
        started_at=sample_timestamp
    )

    result = trace.to_dict()

    assert result["schema_version"] == 1
    assert result["run_id"] == "run-123"
    assert result["started_at"] == sample_timestamp.isoformat()
    assert result["completed_at"] is None
    assert result["status"] == "running"
    assert result["events"] == []


def test_execution_trace_serializes_events_in_order(sample_timestamp):
    event1 = TraceEvent(
        "event-1", "run_started", sample_timestamp
    )

    event2 = TraceEvent(
        "event-2", "model_call", sample_timestamp
    )

    trace = ExecutionTrace(
        "run-123",
        sample_timestamp,
        events=[event1, event2]
    )

    result = trace.to_dict()

    assert len(result["events"]) == 2
    assert result["events"][0]["event_id"] == "event-1"
    assert result["events"][1]["event_id"] == "event-2"


def test_execution_trace_serializes_completed_trace(sample_timestamp):
    trace = ExecutionTrace("run-123", sample_timestamp)

    trace.finish("completed")

    result = trace.to_dict()

    assert result["status"] == "completed"
    assert result["completed_at"] is not None
    assert isinstance(result["completed_at"], str)


def test_execution_trace_to_dict_does_not_modify_original(sample_timestamp):
    event = TraceEvent(
        "event-1",
        "run_started",
        sample_timestamp,
        event_details={"value": 42}
    )

    trace = ExecutionTrace(
        "run-123",
        sample_timestamp,
        events=[event]
    )

    trace.to_dict()

    assert isinstance(trace.started_at, datetime)
    assert isinstance(event.timestamp, datetime)
    assert trace.events[0] is event
    assert event.event_details == {"value": 42}


def test_execution_trace_to_dict_is_json_serializable(sample_timestamp):
    event = TraceEvent(
        "event-1",
        "tool_execution",
        sample_timestamp,
        event_details={"result": [1, 2, 3]}
    )

    trace = ExecutionTrace(
        "run-123",
        sample_timestamp,
        events=[event]
    )

    result = trace.to_dict()

    serialized_json = json.dumps(
        result,
        allow_nan=False,
        indent=2
    )

    assert isinstance(serialized_json, str)
    assert json.loads(serialized_json) == result