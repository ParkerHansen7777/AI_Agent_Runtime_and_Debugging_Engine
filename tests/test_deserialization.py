
import math
from datetime import datetime, timezone

import pytest

from agent_runtime.tracing import _deserialize_value


# Primitive values

@pytest.mark.parametrize(
    "value",
    [
        None,
        True,
        False,
        0,
        42,
        -10,
        3.14,
        "hello",
        "",
    ],
)
def test_deserialize_primitive_values(value):
    assert _deserialize_value(value) == value


# Float validation

@pytest.mark.parametrize(
    "value",
    [
        math.nan,
        math.inf,
        -math.inf,
    ],
)
def test_deserialize_rejects_non_finite_floats(value):
    with pytest.raises(ValueError):
        _deserialize_value(value)


def test_deserialize_finite_float():
    assert _deserialize_value(3.14) == 3.14


# List validation

def test_deserialize_list():
    value = [1, "hello", True, None]

    result = _deserialize_value(value)

    assert result == value
    assert result is not value


def test_deserialize_nested_lists():
    value = [[1, 2], [3, [4, 5]]]

    result = _deserialize_value(value)

    assert result == value
    assert result is not value
    assert result[1] is not value[1]
    assert result[1][1] is not value[1][1]


def test_deserialize_list_with_invalid_value():
    value = [1, "hello", object()]

    with pytest.raises(TypeError):
        _deserialize_value(value)


# Dictionary validation

def test_deserialize_dictionary():
    value = {
        "name": "search",
        "count": 5,
        "enabled": True,
    }

    result = _deserialize_value(value)

    assert result == value
    assert result is not value


def test_deserialize_nested_dictionary():
    value = {
        "tool": {
            "name": "search",
            "arguments": {
                "query": "weather",
            },
        }
    }

    result = _deserialize_value(value)

    assert result == value
    assert result is not value
    assert result["tool"] is not value["tool"]
    assert result["tool"]["arguments"] is not value["tool"]["arguments"]


def test_deserialize_rejects_non_string_dictionary_keys():
    value = {
        123: "invalid key",
    }

    with pytest.raises(TypeError):
        _deserialize_value(value)


def test_deserialize_rejects_invalid_nested_dictionary_key():
    value = {
        "outer": {
            123: "invalid key",
        }
    }

    with pytest.raises(TypeError):
        _deserialize_value(value)


def test_deserialize_dictionary_with_invalid_value():
    value = {
        "invalid": object(),
    }

    with pytest.raises(TypeError):
        _deserialize_value(value)


# Unsupported types

def test_deserialize_rejects_datetime():
    value = datetime.now(timezone.utc)

    with pytest.raises(TypeError):
        _deserialize_value(value)


def test_deserialize_rejects_unsupported_object():
    with pytest.raises(TypeError):
        _deserialize_value(object())


# Original input preservation

def test_deserialize_does_not_modify_original_input():
    value = {
        "tool": {
            "name": "search",
            "arguments": [1, 2, 3],
        }
    }

    original = {
        "tool": {
            "name": "search",
            "arguments": [1, 2, 3],
        }
    }

    result = _deserialize_value(value)

    assert value == original
    assert result == original
    assert result is not value
    assert result["tool"] is not value["tool"]
    assert result["tool"]["arguments"] is not value["tool"]["arguments"]
