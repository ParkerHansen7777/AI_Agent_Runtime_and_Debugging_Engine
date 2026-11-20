
import pytest

from agent_runtime.storage import TraceStorage


def test_list_traces_returns_all_json_trace_ids(tmp_path):
    storage = TraceStorage(tmp_path)

    (tmp_path / "run-001.json").write_text("{}", encoding="utf-8")
    (tmp_path / "run-002.json").write_text("{}", encoding="utf-8")
    (tmp_path / "run-003.json").write_text("{}", encoding="utf-8")

    result = storage.list_traces()

    assert result == ["run-001", "run-002", "run-003"]


def test_list_traces_returns_alphabetically_sorted_ids(tmp_path):
    storage = TraceStorage(tmp_path)

    (tmp_path / "run-003.json").write_text("{}", encoding="utf-8")
    (tmp_path / "run-001.json").write_text("{}", encoding="utf-8")
    (tmp_path / "run-002.json").write_text("{}", encoding="utf-8")

    result = storage.list_traces()

    assert result == ["run-001", "run-002", "run-003"]


def test_list_traces_ignores_non_json_files(tmp_path):
    storage = TraceStorage(tmp_path)

    (tmp_path / "run-001.json").write_text("{}", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("Some notes", encoding="utf-8")
    (tmp_path / "config.yaml").write_text("setting: true", encoding="utf-8")

    result = storage.list_traces()

    assert result == ["run-001"]


def test_list_traces_ignores_directories_ending_in_json(tmp_path):
    storage = TraceStorage(tmp_path)

    (tmp_path / "run-001.json").write_text("{}", encoding="utf-8")
    (tmp_path / "fake-trace.json").mkdir()

    result = storage.list_traces()

    assert result == ["run-001"]


def test_list_traces_returns_empty_list_for_empty_directory(tmp_path):
    storage = TraceStorage(tmp_path)

    result = storage.list_traces()

    assert result == []


def test_list_traces_returns_empty_list_for_non_json_files(tmp_path):
    storage = TraceStorage(tmp_path)

    (tmp_path / "notes.txt").write_text("Some notes", encoding="utf-8")
    (tmp_path / "config.yaml").write_text("setting: true", encoding="utf-8")

    result = storage.list_traces()

    assert result == []


def test_list_traces_does_not_deserialize_json_files(tmp_path):
    storage = TraceStorage(tmp_path)

    # Deliberately malformed JSON
    (tmp_path / "run-001.json").write_text("{invalid json", encoding="utf-8")

    result = storage.list_traces()

    assert result == ["run-001"]
