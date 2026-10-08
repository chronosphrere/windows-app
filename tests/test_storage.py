"""Tests for JSON note storage logic."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from notes.storage import Note, NoteStore, StorageError


@pytest.fixture
def store(tmp_path: Path) -> NoteStore:
    return NoteStore(data_dir=tmp_path / "MyNotes")


def test_load_missing_file_returns_empty(store: NoteStore) -> None:
    notes = store.load()
    assert notes == []
    assert store.list_notes() == []


def test_save_and_load_roundtrip(store: NoteStore) -> None:
    first = Note.create(title="Shopping", content="milk\nbread")
    second = Note.create(title="Ideas", content="build a notes app")
    store.upsert(first)
    store.upsert(second)
    store.save()

    reloaded = NoteStore(data_dir=store.data_dir)
    notes = reloaded.load()
    assert {n.id for n in notes} == {first.id, second.id}
    by_id = {n.id: n for n in notes}
    assert by_id[first.id].title == "Shopping"
    assert by_id[first.id].content == "milk\nbread"
    assert by_id[second.id].title == "Ideas"


def test_list_notes_sorted_by_title(store: NoteStore) -> None:
    store.upsert(Note.create(title="zeta", content=""))
    store.upsert(Note.create(title="Alpha", content=""))
    store.upsert(Note.create(title="beta", content=""))
    titles = [n.title for n in store.list_notes()]
    assert titles == ["Alpha", "beta", "zeta"]


def test_delete_note(store: NoteStore) -> None:
    note = Note.create(title="temp", content="x")
    store.upsert(note)
    store.save()
    assert store.delete(note.id) is True
    store.save()

    reloaded = NoteStore(data_dir=store.data_dir)
    assert reloaded.load() == []
    assert store.delete("missing-id") is False


def test_upsert_updates_existing_note(store: NoteStore) -> None:
    note = Note.create(title="Draft", content="v1")
    store.upsert(note)
    store.save()

    note.title = "Final"
    note.content = "v2"
    store.upsert(note)
    store.save()

    reloaded = NoteStore(data_dir=store.data_dir).load()
    assert len(reloaded) == 1
    assert reloaded[0].title == "Final"
    assert reloaded[0].content == "v2"


def test_load_invalid_json_raises(store: NoteStore) -> None:
    store.ensure_data_dir()
    store.notes_path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(StorageError, match="not valid JSON"):
        store.load()


def test_load_unexpected_format_raises(store: NoteStore) -> None:
    store.ensure_data_dir()
    store.notes_path.write_text(json.dumps(["oops"]), encoding="utf-8")
    with pytest.raises(StorageError, match="unexpected format"):
        store.load()


def test_save_writes_expected_json_shape(store: NoteStore) -> None:
    note = Note(id="fixed-id", title="Hello", content="World")
    store.upsert(note)
    store.save()

    payload = json.loads(store.notes_path.read_text(encoding="utf-8"))
    assert payload == {
        "notes": [
            {"id": "fixed-id", "title": "Hello", "content": "World"},
        ]
    }


def test_default_data_dir_uses_qstandardpaths(qapp, tmp_path: Path, monkeypatch) -> None:
    """Default path comes from QStandardPaths, not the source tree."""
    from PySide6.QtCore import QStandardPaths

    def fake_writable(_location):
        return str(tmp_path / "AppData" / "MyNotes")

    monkeypatch.setattr(QStandardPaths, "writableLocation", fake_writable)
    store = NoteStore()
    assert store.data_dir == tmp_path / "AppData" / "MyNotes"

    project_root = Path(__file__).resolve().parents[1]
    resolved = store.data_dir.resolve()
    assert resolved != project_root
    assert project_root not in resolved.parents


def test_default_data_dir_empty_location_raises(qapp, monkeypatch) -> None:
    from PySide6.QtCore import QStandardPaths

    monkeypatch.setattr(QStandardPaths, "writableLocation", lambda _loc: "")
    with pytest.raises(StorageError, match="writable application data directory"):
        NoteStore()
