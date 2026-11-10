
import pytest
from datetime import datetime, timezone

from agent_runtime.tracing import TraceEvent, ExecutionTrace


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
