"""JSON-backed note persistence in a per-user application data directory."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QStandardPaths


class StorageError(Exception):
    """Raised when notes cannot be loaded from or saved to disk."""


@dataclass
class Note:
    """A single note with a stable id, title, and body text."""

    id: str
    title: str = ""
    content: str = ""

    @staticmethod
    def create(title: str = "Untitled", content: str = "") -> Note:
        return Note(id=str(uuid.uuid4()), title=title, content=content)


@dataclass
class NoteStore:
    """Load and save notes as JSON under the app data directory."""

    data_dir: Optional[Path] = None
    _notes: dict[str, Note] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if self.data_dir is None:
            self.data_dir = self._default_data_dir()
        self.data_dir = Path(self.data_dir)

    def _default_data_dir(self) -> Path:
        """Resolve a writable per-user location via QStandardPaths.

        Uses AppDataLocation so notes live in the platform application-data
        directory (for example under %LOCALAPPDATA% on Windows), not beside
        the source tree or executable. Callers should set the Qt application
        and organization names before constructing a store with the default path.
        """
        base = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation
        )
        if not base:
            raise StorageError(
                "Could not determine a writable application data directory."
            )
        return Path(base)

    @property
    def notes_path(self) -> Path:
        return self.data_dir / "notes.json"

    def ensure_data_dir(self) -> None:
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError(
                f"Could not create data directory '{self.data_dir}': {exc}"
            ) from exc

    def load(self) -> list[Note]:
        """Load notes from disk. Missing file yields an empty list."""
        path = self.notes_path
        if not path.exists():
            self._notes = {}
            return []

        try:
            raw = path.read_text(encoding="utf-8")
            payload = json.loads(raw)
        except OSError as exc:
            raise StorageError(f"Could not read notes file '{path}': {exc}") from exc
        except json.JSONDecodeError as exc:
            raise StorageError(
                f"Notes file '{path}' is not valid JSON: {exc}"
            ) from exc

        if not isinstance(payload, dict) or "notes" not in payload:
            raise StorageError(
                f"Notes file '{path}' has an unexpected format "
                "(expected an object with a 'notes' list)."
            )

        notes_list = payload["notes"]
        if not isinstance(notes_list, list):
            raise StorageError(
                f"Notes file '{path}' has an unexpected format "
                "('notes' must be a list)."
            )

        loaded: dict[str, Note] = {}
        for item in notes_list:
            if not isinstance(item, dict):
                raise StorageError(
                    f"Notes file '{path}' contains an invalid note entry."
                )
            note_id = item.get("id")
            if not note_id or not isinstance(note_id, str):
                raise StorageError(
                    f"Notes file '{path}' contains a note without a valid id."
                )
            loaded[note_id] = Note(
                id=note_id,
                title=str(item.get("title", "")),
                content=str(item.get("content", "")),
            )

        self._notes = loaded
        return self.list_notes()

    def list_notes(self) -> list[Note]:
        """Return notes sorted by title (case-insensitive), then id."""
        return sorted(
            self._notes.values(),
            key=lambda n: (n.title.lower(), n.id),
        )

    def get(self, note_id: str) -> Optional[Note]:
        return self._notes.get(note_id)

    def upsert(self, note: Note) -> None:
        self._notes[note.id] = note

    def delete(self, note_id: str) -> bool:
        if note_id not in self._notes:
            return False
        del self._notes[note_id]
        return True

    def save(self) -> None:
        """Persist the current notes to JSON."""
        self.ensure_data_dir()
        path = self.notes_path
        payload = {
            "notes": [asdict(note) for note in self.list_notes()],
        }
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        try:
            path.write_text(text, encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"Could not save notes to '{path}': {exc}") from exc
