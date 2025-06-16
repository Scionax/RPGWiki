import os
import sys
from typing import Dict

from PyQt5.QtCore import Qt, QEvent, QUrl

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
    QFileDialog,
    QMessageBox,
    QSplitter,
    QAction,
    QToolBar,
)

from .formatter import format_content

from .parser import scan_folder, scan_headers, KeywordTarget, HeaderEntry
from .search import SearchDialog
from .config import Config, load_config, save_config


def _is_word_char(ch: str) -> bool:
    return ch.isalnum() or ch == "_"


class WikiApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RPG Wiki")
        self.resize(1000, 600)

        self.config_data: Config = load_config()
        self.keyword_map: Dict[str, KeywordTarget] = {}
        self.headers: list[HeaderEntry] = []
        self.search_dialog: SearchDialog | None = None

        self.history_back: list[str] = []
        self.history_forward: list[str] = []
        self.current_file: str | None = None

        self._build_gui()
        self.installEventFilter(self)
        self._load_saved_folders()

    # Event filter for mouse and keyboard navigation
    def eventFilter(self, obj, event):  # type: ignore[override]
        if event.type() == QEvent.MouseButtonPress:
            if event.button() in (Qt.BackButton, Qt.XButton1):
                self.go_back()
                return True
            if event.button() in (Qt.ForwardButton, Qt.XButton2):
                self.go_forward()
                return True
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Left:
                self.go_back()
                return True
            if event.key() == Qt.Key_Right:
                self.go_forward()
                return True
            if event.key() in (Qt.Key_Space, Qt.Key_Up):
                self.show_search()
                return True
        return super().eventFilter(obj, event)

    def _build_gui(self) -> None:
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        load_world = QAction("Load World Folder", self)
        load_world.triggered.connect(self.load_world)
        file_menu.addAction(load_world)

        load_campaign = QAction("Load Campaign Folder", self)
        load_campaign.triggered.connect(self.load_campaign)
        file_menu.addAction(load_campaign)

        file_menu.addSeparator()

        rescan_action = QAction("Rescan", self)
        rescan_action.triggered.connect(self.rescan)
        file_menu.addAction(rescan_action)

        search_action = QAction("Search", self)
        search_action.triggered.connect(self.show_search)
        file_menu.addAction(search_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        toolbar = QToolBar()
        self.addToolBar(toolbar)

        self.back_action = QAction("Back", self)
        self.back_action.triggered.connect(self.go_back)
        toolbar.addAction(self.back_action)

        self.forward_action = QAction("Forward", self)
        self.forward_action.triggered.connect(self.go_forward)
        toolbar.addAction(self.forward_action)

        splitter = QSplitter()
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemExpanded.connect(self._on_expand)
        self.tree.itemClicked.connect(self._on_select)
        splitter.addWidget(self.tree)

        self.text = QTextBrowser()
        self.text.setOpenExternalLinks(False)
        self.text.anchorClicked.connect(self._on_anchor_clicked)
        splitter.addWidget(self.text)

        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)
        self._update_nav_actions()

    def show_search(self) -> None:
        if not self.search_dialog:
            self.search_dialog = SearchDialog(self)
        self.search_dialog.open()

    def _update_nav_actions(self) -> None:
        self.back_action.setEnabled(bool(self.history_back))
        self.forward_action.setEnabled(bool(self.history_forward))

    def _load_saved_folders(self) -> None:
        if self.config_data.world_dir:
            self._add_folder_to_tree(self.config_data.world_dir, "World")
        if self.config_data.campaign_dir:
            self._add_folder_to_tree(self.config_data.campaign_dir, "Campaign")
        self.rescan()

    def _add_folder_to_tree(self, folder: str, tag: str) -> None:
        node = QTreeWidgetItem(self.tree, [f"{tag}: {folder}"])
        node.setData(0, Qt.UserRole, (folder, "dir"))
        self._populate_tree(node, folder)
        node.setExpanded(True)

    def _populate_tree(self, parent: QTreeWidgetItem, path: str) -> None:
        try:
            entries = sorted(os.listdir(path))
        except OSError:
            return

        dirs: list[tuple[str, str]] = []
        files: list[tuple[str, str]] = []
        for entry in entries:
            full = os.path.join(path, entry)
            if os.path.isdir(full):
                if self._has_md_files(full):
                    dirs.append((entry, full))
            elif entry.lower().endswith(".md") and not entry.startswith("_"):
                files.append((entry, full))

        for entry, full in dirs:
            child = QTreeWidgetItem(parent, [entry])
            child.setData(0, Qt.UserRole, (full, "dir"))
            child.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
        for entry, full in files:
            name = os.path.splitext(entry)[0]
            child = QTreeWidgetItem(parent, [name])
            child.setData(0, Qt.UserRole, (full, "file"))

    def _has_md_files(self, path: str) -> bool:
        for root, _, files in os.walk(path):
            for f in files:
                if f.lower().endswith(".md") and not f.startswith("_"):
                    return True
        return False

    def _on_expand(self, item: QTreeWidgetItem) -> None:
        path, typ = item.data(0, Qt.UserRole)
        if typ == "dir" and item.childCount() == 0:
            self._populate_tree(item, path)

    def _on_select(self, item: QTreeWidgetItem, column: int) -> None:
        path, typ = item.data(0, Qt.UserRole)
        if typ == "file":
            self.open_file(path)

    def load_world(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select World Folder")
        if folder:
            self.config_data.world_dir = folder
            self.tree.clear()
            self._add_folder_to_tree(folder, "World")
            if self.config_data.campaign_dir:
                self._add_folder_to_tree(self.config_data.campaign_dir, "Campaign")
            self.rescan()
            save_config(self.config_data)

    def load_campaign(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Campaign Folder")
        if folder:
            self.config_data.campaign_dir = folder
            self.tree.clear()
            if self.config_data.world_dir:
                self._add_folder_to_tree(self.config_data.world_dir, "World")
            self._add_folder_to_tree(folder, "Campaign")
            self.rescan()
            save_config(self.config_data)

    def rescan(self) -> None:
        self.keyword_map.clear()
        self.headers.clear()
        if self.config_data.world_dir:
            self.keyword_map.update(scan_folder(self.config_data.world_dir))
            self.headers.extend(scan_headers(self.config_data.world_dir))
        if self.config_data.campaign_dir:
            camp_map = scan_folder(self.config_data.campaign_dir)
            self.keyword_map.update(camp_map)
            self.headers.extend(scan_headers(self.config_data.campaign_dir))

    def open_file(self, path: str, add_history: bool = True) -> None:
        if add_history and self.current_file and path != self.current_file:
            self.history_back.append(self.current_file)
            self.history_forward.clear()
        self.current_file = path

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        html = format_content(content, self.keyword_map, self.config_data)
        self.text.setHtml(html)
        self.text.document().clearUndoRedoStacks()
        self._update_nav_actions()

    def go_back(self) -> None:
        if self.history_back:
            last = self.history_back.pop()
            if self.current_file:
                self.history_forward.append(self.current_file)
            self.open_file(last, add_history=False)

    def go_forward(self) -> None:
        if self.history_forward:
            nxt = self.history_forward.pop()
            if self.current_file:
                self.history_back.append(self.current_file)
            self.open_file(nxt, add_history=False)


    def _on_anchor_clicked(self, url: QUrl) -> None:
        word = url.toString()
        target = self.keyword_map.get(word)
        if not target and not self.config_data.case_sensitive:
            lower = word.lower()
            for kw, tgt in self.keyword_map.items():
                if kw.lower() == lower:
                    target = tgt
                    break
        if target:
            self.open_file(target.file)
            anchor = f"ln{target.line}"
            self.text.scrollToAnchor(anchor)


def main() -> None:
    app = QApplication(sys.argv)
    win = WikiApp()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
