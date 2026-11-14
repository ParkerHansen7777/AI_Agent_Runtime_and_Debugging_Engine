
import copy
import math
from datetime import datetime, timezone, timedelta

import pytest

from agent_runtime.tracing import TraceEvent


def make_event_data():
    return {
        "event_id": "event-123",
        "event_type": "tool_execution",
        "timestamp": "2026-11-13T12:30:00+00:00",
        "iteration": 2,
        "duration_ms": 125.5,
        "status": "success",
        "event_details": {
            "tool_name": "search",
            "arguments": {
                "query": "Python testing"
            },
            "result_count": 5
        }
    }


# Successful reconstruction

def test_from_dict_creates_trace_event():
    data = make_event_data()

    event = TraceEvent.from_dict(data)

    assert isinstance(event, TraceEvent)
    assert event.event_id == "event-123"
    assert event.event_type == "tool_execution"
    assert event.timestamp == datetime(
        2026, 11, 13, 12, 30, tzinfo=timezone.utc
    )
    assert event.iteration == 2
    assert event.duration_ms == 125.5
    assert event.status == "success"
    assert event.event_details["tool_name"] == "search"


def test_from_dict_preserves_none_values():
    data = make_event_data()
    data["iteration"] = None
    data["duration_ms"] = None

    event = TraceEvent.from_dict(data)

    assert event.iteration is None
    assert event.duration_ms is None


def test_from_dict_preserves_timezone_offset():
    data = make_event_data()
    data["timestamp"] = "2026-11-13T12:30:00-05:00"

    event = TraceEvent.from_dict(data)

    assert event.timestamp.utcoffset() == timedelta(hours=-5)


def test_from_dict_does_not_modify_input():
    data = make_event_data()
    original = copy.deepcopy(data)

    TraceEvent.from_dict(data)

    assert data == original


# Dictionary structure validation

def test_from_dict_rejects_non_dictionary():
    with pytest.raises(TypeError):
        TraceEvent.from_dict("not a dictionary")


def test_from_dict_rejects_missing_key():
    data = make_event_data()
    del data["event_id"]

    with pytest.raises(ValueError):
        TraceEvent.from_dict(data)


def test_from_dict_rejects_unexpected_key():
    data = make_event_data()
    data["unexpected"] = "value"

    with pytest.raises(ValueError):
        TraceEvent.from_dict(data)


# String validation

@pytest.mark.parametrize(
    "field",
    ["event_id", "event_type", "status"]
)
def test_from_dict_rejects_non_string_fields(field):
    data = make_event_data()
    data[field] = 123

    with pytest.raises(TypeError):
        TraceEvent.from_dict(data)


# Iteration validation

@pytest.mark.parametrize(
    "value",
    [True, False, "2", 2.5, []]
)
def test_from_dict_rejects_invalid_iteration(value):
    data = make_event_data()
    data["iteration"] = value

    with pytest.raises(TypeError):
        TraceEvent.from_dict(data)


# Duration validation

@pytest.mark.parametrize(
    "value",
    [True, False, "125.5", [], {}]
)
def test_from_dict_rejects_invalid_duration(value):
    data = make_event_data()
    data["duration_ms"] = value

    with pytest.raises(TypeError):
        TraceEvent.from_dict(data)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_from_dict_rejects_non_finite_duration(value):
    data = make_event_data()
    data["duration_ms"] = value

    with pytest.raises(ValueError):
        TraceEvent.from_dict(data)


# Timestamp validation

def test_from_dict_rejects_non_string_timestamp():
    data = make_event_data()
    data["timestamp"] = 123

    with pytest.raises(TypeError):
        TraceEvent.from_dict(data)


def test_from_dict_rejects_invalid_timestamp():
    data = make_event_data()
    data["timestamp"] = "not-a-timestamp"

    with pytest.raises(ValueError):
        TraceEvent.from_dict(data)


# Event details validation

@pytest.mark.parametrize(
    "value",
    ["not a dictionary", 123, 12.5, None, []]
)
def test_from_dict_rejects_non_dictionary_event_details(value):
    data = make_event_data()
    data["event_details"] = value

    with pytest.raises(TypeError):
        TraceEvent.from_dict(data)


def test_from_dict_rejects_non_string_event_details_key():
    data = make_event_data()
    data["event_details"] = {123: "invalid key"}

    with pytest.raises(TypeError):
        TraceEvent.from_dict(data)


def test_from_dict_rejects_unsupported_nested_event_details_value():
    data = make_event_data()
    data["event_details"] = {
        "nested": {
            "unsupported": (1, 2, 3)
        }
    }

    with pytest.raises(TypeError):
        TraceEvent.from_dict(data)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_from_dict_rejects_non_finite_nested_float(value):
    data = make_event_data()
    data["event_details"] = {
        "nested": {
            "value": value
        }
    }

    with pytest.raises(ValueError):
        TraceEvent.from_dict(data)
