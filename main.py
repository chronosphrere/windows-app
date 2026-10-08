#!/usr/bin/env python3
"""Entry point for the My Notes desktop application."""

import sys

from PySide6.QtWidgets import QApplication

from notes.ui import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("My Notes")
    app.setOrganizationName("MyNotes")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
