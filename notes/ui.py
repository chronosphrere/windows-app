"""Main window UI for My Notes."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from notes.storage import Note, NoteStore, StorageError


class MainWindow(QMainWindow):
    """Notes browser with list, editor, and New / Save / Delete actions."""

    def __init__(self, store: Optional[NoteStore] = None) -> None:
        super().__init__()
        self.store = store or NoteStore()
        self._current_id: Optional[str] = None

        self.setWindowTitle("My Notes")
        self.resize(900, 560)
        self._build_ui()
        self._load_notes()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("Notes"))
        self.notes_list = QListWidget()
        self.notes_list.currentItemChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self.notes_list)

        button_row = QHBoxLayout()
        self.new_button = QPushButton("New")
        self.save_button = QPushButton("Save")
        self.delete_button = QPushButton("Delete")
        self.new_button.clicked.connect(self._on_new)
        self.save_button.clicked.connect(self._on_save)
        self.delete_button.clicked.connect(self._on_delete)
        button_row.addWidget(self.new_button)
        button_row.addWidget(self.save_button)
        button_row.addWidget(self.delete_button)
        left_layout.addLayout(button_row)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel("Title"))
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Note title")
        right_layout.addWidget(self.title_edit)
        right_layout.addWidget(QLabel("Content"))
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Write your note here…")
        right_layout.addWidget(self.content_edit)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        self._set_editor_enabled(False)

    def _set_editor_enabled(self, enabled: bool) -> None:
        self.title_edit.setEnabled(enabled)
        self.content_edit.setEnabled(enabled)
        self.save_button.setEnabled(enabled)
        self.delete_button.setEnabled(enabled)

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)

    def _load_notes(self) -> None:
        try:
            notes = self.store.load()
        except StorageError as exc:
            self._show_error("Load failed", str(exc))
            notes = []

        self._populate_list(notes)
        if notes:
            self.notes_list.setCurrentRow(0)
        else:
            self._current_id = None
            self._clear_editor()
            self._set_editor_enabled(False)

    def _populate_list(self, notes: list[Note]) -> None:
        self.notes_list.blockSignals(True)
        self.notes_list.clear()
        for note in notes:
            item = QListWidgetItem(note.title or "Untitled")
            item.setData(Qt.ItemDataRole.UserRole, note.id)
            self.notes_list.addItem(item)
        self.notes_list.blockSignals(False)

    def _clear_editor(self) -> None:
        self.title_edit.clear()
        self.content_edit.clear()

    def _show_note(self, note: Note) -> None:
        self._current_id = note.id
        self.title_edit.setText(note.title)
        self.content_edit.setPlainText(note.content)
        self._set_editor_enabled(True)

    def _on_selection_changed(
        self,
        current: Optional[QListWidgetItem],
        _previous: Optional[QListWidgetItem],
    ) -> None:
        if current is None:
            self._current_id = None
            self._clear_editor()
            self._set_editor_enabled(False)
            return

        note_id = current.data(Qt.ItemDataRole.UserRole)
        note = self.store.get(note_id)
        if note is None:
            self._show_error("Load failed", "The selected note could not be found.")
            return
        self._show_note(note)

    def _on_new(self) -> None:
        title, ok = QInputDialog.getText(self, "New note", "Title:")
        if not ok:
            return
        title = title.strip() or "Untitled"
        note = Note.create(title=title, content="")
        self.store.upsert(note)
        try:
            self.store.save()
        except StorageError as exc:
            self.store.delete(note.id)
            self._show_error("Save failed", str(exc))
            return

        self._populate_list(self.store.list_notes())
        self._select_by_id(note.id)

    def _on_save(self) -> None:
        if self._current_id is None:
            return

        note = self.store.get(self._current_id)
        if note is None:
            self._show_error("Save failed", "The selected note could not be found.")
            return

        note.title = self.title_edit.text().strip() or "Untitled"
        note.content = self.content_edit.toPlainText()
        self.store.upsert(note)

        try:
            self.store.save()
        except StorageError as exc:
            self._show_error("Save failed", str(exc))
            return

        self._populate_list(self.store.list_notes())
        self._select_by_id(note.id)

    def _on_delete(self) -> None:
        if self._current_id is None:
            return

        note = self.store.get(self._current_id)
        label = note.title if note else "this note"
        reply = QMessageBox.question(
            self,
            "Delete note",
            f'Delete "{label}"? This cannot be undone.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        note_id = self._current_id
        if not self.store.delete(note_id):
            self._show_error("Delete failed", "The selected note could not be found.")
            return

        try:
            self.store.save()
        except StorageError as exc:
            # Restore in-memory state if disk write failed.
            if note is not None:
                self.store.upsert(note)
            self._show_error("Save failed", str(exc))
            return

        self._populate_list(self.store.list_notes())
        if self.notes_list.count() > 0:
            self.notes_list.setCurrentRow(0)
        else:
            self._current_id = None
            self._clear_editor()
            self._set_editor_enabled(False)

    def _select_by_id(self, note_id: str) -> None:
        for row in range(self.notes_list.count()):
            item = self.notes_list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == note_id:
                self.notes_list.setCurrentItem(item)
                return
