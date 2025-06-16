"""Widget for searching headers across loaded folders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
)

from .parser import HeaderEntry


@dataclass
class SearchResult:
    entry: HeaderEntry


class SearchDialog(QDialog):
    """Modal dialog used for header search."""

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setWindowTitle("Search Headers")
        self.setModal(True)

        layout = QVBoxLayout(self)
        self.edit = QLineEdit()
        self.edit.returnPressed.connect(self.perform_search)
        layout.addWidget(self.edit)

        self.list = QListWidget()
        self.list.itemActivated.connect(self._activate)
        layout.addWidget(self.list)

        self.results: List[HeaderEntry] = []

    def open(self) -> None:  # type: ignore[override]
        self.edit.clear()
        self.list.clear()
        self.results = []
        super().open()
        self.edit.setFocus()

    def perform_search(self) -> None:
        query = self.edit.text().strip()
        if not query:
            return
        app = self.parent()  # WikiApp
        case = app.config_data.case_sensitive
        search = query if case else query.lower()
        self.list.clear()
        full: List[HeaderEntry] = []
        partial: List[HeaderEntry] = []
        for entry in app.headers:
            text = entry.text if case else entry.text.lower()
            if text == search:
                full.append(entry)
            elif search in text:
                partial.append(entry)
        partial = partial[:10]
        self.results = full + partial
        for idx, item in enumerate(self.results[:9], 1):
            display = (
                f"{idx}. <span style='background-color:#eef; padding:1px 4px; "
                f"border-radius:3px'>{item.file.split('/')[-1]}</span> "
                f"<b>{item.text}</b> - {item.preview}"
            )
            lw_item = QListWidgetItem()
            lw_item.setData(Qt.UserRole, item)
            lw_item.setText(display)
            lw_item.setTextAlignment(Qt.AlignLeft)
            self.list.addItem(lw_item)

    def keyPressEvent(self, event):  # type: ignore[override]
        if Qt.Key_1 <= event.key() <= Qt.Key_9:
            idx = event.key() - Qt.Key_1
            if idx < len(self.results):
                self._open(self.results[idx])
                return
        super().keyPressEvent(event)

    def _activate(self, item: QListWidgetItem) -> None:
        entry = item.data(Qt.UserRole)
        if entry:
            self._open(entry)

    def _open(self, entry: HeaderEntry) -> None:
        app = self.parent()
        app.open_file(entry.file)
        anchor = f"ln{entry.line}"
        app.text.scrollToAnchor(anchor)
        self.close()

