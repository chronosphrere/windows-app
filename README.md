# My Notes

A minimal Windows desktop notes app built with **Python** and **PySide6**.

Create, edit, save, and delete notes. Data is stored as JSON in a writable
per-user application data directory (via `QStandardPaths`), not next to the
source code or executable. No administrator privileges are required.

## Project structure

```
main.py                 Entry point — starts the Qt application
notes/
  __init__.py           Package marker
  storage.py            Note model + JSON load/save (separated from UI)
  ui.py                 Main window: list, title, editor, buttons
tests/
  conftest.py           Shared pytest fixtures (QApplication)
  test_storage.py       Unit tests for storage logic
requirements.txt        Runtime and test dependencies
README.md               This file
```

## Requirements

- Python 3.10+
- Windows (also runs on macOS/Linux for development)
- Dependencies from `requirements.txt` (PySide6, pytest)

## Setup

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run the app

```bash
python main.py
```

The window title is **My Notes**. Use:

- **New** — create a note
- **Save** — write the current title and content to disk
- **Delete** — remove the selected note (asks for confirmation)

### Where notes are stored

Notes are saved to `notes.json` under the platform path from
`QStandardPaths.AppDataLocation`.

On Windows this is typically under `%LOCALAPPDATA%` or `%APPDATA%` (for example
`C:\Users\<you>\AppData\Local\MyNotes\My Notes\notes.json`). The exact path
depends on the organization and application names registered with Qt in
`main.py`.

If loading or saving fails, the app shows a clear error dialog.

## Run tests

```bash
pytest
```

Tests cover the storage layer only (create, update, delete, JSON round-trip,
invalid file handling, and default path resolution via `QStandardPaths`).
They use a temporary directory so they do not touch your real notes.
