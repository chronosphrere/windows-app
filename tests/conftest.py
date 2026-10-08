"""Shared pytest fixtures."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Ensure a QApplication exists for Qt APIs used in storage tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app
