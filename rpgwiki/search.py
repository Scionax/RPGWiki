"""Search page displayed inside the main content area."""

from __future__ import annotations

from typing import List, TYPE_CHECKING

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QTextBrowser

from .parser import HeaderEntry

if TYPE_CHECKING:  # pragma: no cover - used for type hints
    from .gui import WikiApp


class SearchPage(QWidget):
    """Widget used for searching headers within the loaded folders."""

    def __init__(self, parent) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.edit = QLineEdit()
        self.edit.returnPressed.connect(self.perform_search)
        layout.addWidget(self.edit)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(False)
        self.browser.anchorClicked.connect(self._activate)
        layout.addWidget(self.browser)

        self.results: List[HeaderEntry] = []

    def open(self) -> None:
        """Prepare the widget for a new search and focus the edit box."""
        self.edit.clear()
        self.browser.clear()
        self.results = []
        self.edit.setFocus()

    def perform_search(self) -> None:
        query = self.edit.text().strip()
        if not query:
            return
        app: WikiApp = self.window()  # type: ignore[assignment]
        case = app.config_data.case_sensitive
        search = query if case else query.lower()
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
        lines: List[str] = []
        for idx, item in enumerate(self.results[:9], 1):
            filename = item.file.split("/")[-1]
            line = (
                f"<p><a href='{idx-1}' style='display:block; text-decoration:none; position:relative'>"
                f"<span style='font-size:18px; font-weight:bold'>{item.text}</span>"
                f"<span style='position:absolute; right:0; background-color:#eef; padding:1px 4px; border-radius:3px'>{filename}</span>"
                f"</a><br>"
                f"<span style='font-size:12px'>{item.preview}</span></p>"
            )
            lines.append(line)
        self.browser.setHtml("\n".join(lines))

    def _activate(self, url: QUrl) -> None:
        try:
            idx = int(url.toString())
        except ValueError:
            return
        if 0 <= idx < len(self.results):
            self._open(self.results[idx])

    def _open(self, entry: HeaderEntry) -> None:
        app: WikiApp = self.window()  # type: ignore[assignment]
        app.open_file(entry.file)
        anchor = f"ln{entry.line}"
        app.text.scrollToAnchor(anchor)
        app.show_content()
