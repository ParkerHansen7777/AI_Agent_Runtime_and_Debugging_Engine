
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agent_runtime.storage import TraceStorage
from agent_runtime.tracing import ExecutionTrace


def make_trace(run_id="run-123"):
    return ExecutionTrace(
        run_id=run_id,
        started_at=datetime(2026, 11, 19, tzinfo=timezone.utc),
    )


# __init__ tests

def test_init_creates_directory(tmp_path):
    directory = tmp_path / "nested" / "traces"

    storage = TraceStorage(directory)

    assert storage.directory == directory
    assert directory.exists()
    assert directory.is_dir()


def test_init_accepts_string_path(tmp_path):
    directory = str(tmp_path / "traces")

    storage = TraceStorage(directory)

    assert storage.directory == Path(directory)


def test_init_accepts_path_object(tmp_path):
    storage = TraceStorage(tmp_path)

    assert storage.directory == tmp_path


def test_init_rejects_invalid_directory_type():
    with pytest.raises(TypeError):
        TraceStorage(None)

    with pytest.raises(TypeError):
        TraceStorage(123)


# save tests

def test_save_creates_json_file(tmp_path):
    storage = TraceStorage(tmp_path)
    trace = make_trace()

    filepath = storage.save(trace)

    assert filepath.exists()
    assert filepath.is_file()
    assert filepath.name == "run-123.json"


def test_save_returns_path_object(tmp_path):
    storage = TraceStorage(tmp_path)
    trace = make_trace()

    filepath = storage.save(trace)

    assert isinstance(filepath, Path)
    assert filepath == tmp_path / "run-123.json"


def test_save_writes_valid_json(tmp_path):
    storage = TraceStorage(tmp_path)
    trace = make_trace()

    filepath = storage.save(trace)

    with open(filepath, "r", encoding="utf-8") as file:
        data = json.load(file)

    assert data == trace.to_dict()


def test_save_rejects_invalid_trace_type(tmp_path):
    storage = TraceStorage(tmp_path)

    with pytest.raises(TypeError):
        storage.save({"run_id": "run-123"})


def test_save_rejects_non_string_run_id(tmp_path):
    storage = TraceStorage(tmp_path)
    trace = make_trace()
    trace.run_id = 123

    with pytest.raises(TypeError):
        storage.save(trace)


@pytest.mark.parametrize(
    "run_id",
    [
        "",
        "../outside",
        "run/123",
        "run\\123",
        "run 123",
    ],
)
def test_save_rejects_invalid_run_ids(tmp_path, run_id):
    storage = TraceStorage(tmp_path)
    trace = make_trace(run_id)

    with pytest.raises(ValueError):
        storage.save(trace)


def test_save_rejects_duplicate_run_id(tmp_path):
    storage = TraceStorage(tmp_path)
    trace = make_trace()

    first_filepath = storage.save(trace)
    original_contents = first_filepath.read_text(encoding="utf-8")

    with pytest.raises(FileExistsError):
        storage.save(trace)

    assert first_filepath.read_text(encoding="utf-8") == original_contents


def test_save_does_not_create_file_if_serialization_fails(tmp_path):
    storage = TraceStorage(tmp_path)
    trace = make_trace()

    trace.to_dict = lambda: {"invalid": object()}

    with pytest.raises(TypeError):
        storage.save(trace)

    assert not (tmp_path / "run-123.json").exists()
