"""Left file explorer based on QFileSystemModel."""

import os

from PyQt6.QtCore import Qt, QDir, pyqtSignal
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from app.i18n import t


class FileExplorer(QWidget):
    fileOpened = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.model = None
        self.tree = QTreeView()
        self.path_edit = QLineEdit()
        self.path_edit.returnPressed.connect(self._on_path_entered)

        self._btn_open = QPushButton()
        self._btn_open.clicked.connect(self._choose_folder)

        top = QHBoxLayout()
        top.setSpacing(8)
        self._path_label = QLabel()
        top.addWidget(self._path_label)
        top.addWidget(self.path_edit, 1)
        top.addWidget(self._btn_open)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.addLayout(top)
        layout.addWidget(self.tree)

        self.tree.doubleClicked.connect(self._on_double_click)
        self.retranslate_ui()

    def set_root(self, path):
        if not os.path.isdir(path):
            return
        self.model = QFileSystemModel()
        self.model.setFilter(
            QDir.Filter.NoDotAndDotDot
            | QDir.Filter.AllEntries
            | QDir.Filter.AllDirs
            | QDir.Filter.Files
        )
        self.model.setRootPath(path)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(path))
        self.tree.setColumnWidth(0, 220)
        self.tree.setColumnWidth(1, 90)
        self.tree.setColumnWidth(2, 90)
        self.path_edit.setText(path)

    def _choose_folder(self):
        from PyQt6.QtWidgets import QFileDialog

        path = QFileDialog.getExistingDirectory(
            self, t("explorer.open.folder.title"), self.path_edit.text() or os.getcwd()
        )
        if path:
            self.set_root(path)

    def _on_path_entered(self):
        self.set_root(self.path_edit.text())

    def _on_double_click(self, index):
        if self.model is None:
            return
        path = self.model.filePath(index)
        if os.path.isfile(path):
            self.fileOpened.emit(path)

    def retranslate_ui(self):
        self._path_label.setText(t("explorer.path") + ":")
        self._btn_open.setText(t("explorer.open.folder"))
        self.path_edit.setPlaceholderText(t("explorer.path.placeholder"))

    def retheme(self):
        """Force style refresh on all child widgets so QSS changes take effect."""
        from PyQt6.QtWidgets import QApplication  # noqa: PLC0415
        app = QApplication.instance()
        if app is None:
            return
        # Unpolish + polish forces Qt to re-apply the current stylesheet to
        # this widget and every descendant.  Without it, dock children keep
        # the old theme's cached colours.
        style = app.style()
        for w in (self, self.tree, self.path_edit, self._btn_open, self._path_label):
            style.unpolish(w)
            style.polish(w)
        self.update()
        self.tree.update()
        self.path_edit.update()
