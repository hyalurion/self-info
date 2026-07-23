"""JSON editor (role-aware: i18n content / changelog / generic JSON)."""

import json

from PyQt6.QtCore import pyqtSignal, Qt, QModelIndex, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QToolBar,
    QToolButton,
    QTreeView,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.code_editor import CodeEditor
from app.file_role import (
    ROLE_I18N,
    ROLE_CHANGELOG,
    ROLE_GENERIC_JSON,
    role_label,
)
from app.i18n import t
from app.json_preview import JsonPreviewWidget
from app.theme import get_preview_colors
from app.utils import is_valid_json, minify_json, pretty_json

_RICH_TYPES = ("text", "info", "highlight")


class ChangelogEntryDialog(QDialog):
    """Small dialog to add a {version, date, content} changelog entry."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("json.entry.title"))
        self.resize(460, 320)
        self._version = QLineEdit()
        self._date = QLineEdit()
        self._content = QPlainTextEdit()
        form = QFormLayout()
        form.addRow(t("json.entry.version"), self._version)
        form.addRow(t("json.entry.date"), self._date)
        form.addRow(t("json.entry.content"), self._content)
        buttons = QHBoxLayout()
        ok = QPushButton(t("common.ok"))
        cancel = QPushButton(t("common.cancel"))
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(ok)
        buttons.addWidget(cancel)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)
        self.setLayout(layout)

    def data(self):
        return {
            "version": self._version.text().strip(),
            "date": self._date.text().strip(),
            "content": self._content.toPlainText().strip(),
        }


class JsonEditor(QWidget):
    contentChanged = pyqtSignal()
    message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._file_path = None
        self._modified = False
        self._loading = False
        self._role = ROLE_GENERIC_JSON
        self._lang = None

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(
            [t("json.col.key"), t("json.col.value"), t("json.col.type")]
        )
        self.model.dataChanged.connect(self._on_data_changed)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setColumnWidth(0, 260)
        self.tree_view.setColumnWidth(1, 260)
        self.tree_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self._on_context_menu)
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setUniformRowHeights(True)

        self.text_edit = CodeEditor(mode="json")
        self.text_edit.textChanged.connect(self._on_text_changed)

        self.preview = JsonPreviewWidget()

        self.right_stack = QStackedWidget()
        self.right_stack.addWidget(self.text_edit)
        self.right_stack.addWidget(self.preview)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.tree_view)
        splitter.addWidget(self.right_stack)
        splitter.setSizes([420, 480])

        self.toolbar = QToolBar()
        self._build_toolbar()

        # Debounced preview re-render while editing.
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(300)
        self._preview_timer.timeout.connect(self._render_preview)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.text_edit.find_widget)
        layout.addWidget(splitter, 1)

        QShortcut(QKeySequence.StandardKey.Find, self, self.text_edit.toggle_find)

    # ---------- Toolbar ----------
    def _build_toolbar(self):
        tb = self.toolbar
        self._a_refresh = tb.addAction(t("json.refresh"), self.refresh_tree_from_text)
        self._a_apply = tb.addAction(t("json.apply"), self.apply_tree_to_text)
        tb.addSeparator()
        self._a_format = tb.addAction(t("json.format"), self.format_text)
        self._a_minify = tb.addAction(t("json.minify"), self.minify_text)
        self._a_validate = tb.addAction(t("json.validate"), self.validate)
        tb.addSeparator()
        self._a_expand = tb.addAction(t("json.expand"), self.expand_all)
        self._a_collapse = tb.addAction(t("json.collapse"), self.collapse_all)
        tb.addSeparator()
        self._auto_sync = QCheckBox(t("json.sync"))
        self._auto_sync.setChecked(True)
        tb.addWidget(self._auto_sync)
        tb.addSeparator()
        self._a_find = tb.addAction(t("json.find"), self.text_edit.toggle_find)
        tb.addSeparator()
        self._a_preview = tb.addAction(t("json.preview"), self.toggle_preview)
        tb.addSeparator()
        # Role-specific tools live in a dropdown button.
        self._tools_btn = QToolButton()
        self._tools_btn.setText(t("json.tools"))
        self._tools_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._tools_menu = QMenu(self._tools_btn)
        self._tools_btn.setMenu(self._tools_menu)
        tb.addWidget(self._tools_btn)
        self._rebuild_role_tools()

    def _rebuild_role_tools(self):
        menu = self._tools_menu
        menu.clear()
        self._role_actions = []
        if self._role == ROLE_I18N:
            acts = [
                (t("json.schema.check"), self.validate_schema),
                (t("json.rich.wrap"), lambda: self._transform_rich("wrap")),
                (t("json.rich.unwrap"), lambda: self._transform_rich("unwrap")),
                (t("json.rich.normalize"), lambda: self._transform_rich("normalize")),
            ]
        elif self._role == ROLE_CHANGELOG:
            acts = [
                (t("json.add.entry"), self.add_changelog_entry),
            ]
        else:
            acts = []
        for label, slot in acts:
            a = menu.addAction(label, slot)
            self._role_actions.append(a)
        self._tools_btn.setVisible(bool(acts))

    # ---------- Public interface ----------
    def get_text(self):
        return self.text_edit.toPlainText()

    def set_text(self, text, mark_modified=False):
        self._loading = True
        self.text_edit.setPlainText(text)
        self._loading = False
        self._modified = mark_modified
        if mark_modified:
            self.contentChanged.emit()

    def load_file(self, path, text):
        self._file_path = path
        self.set_text(text, mark_modified=False)
        self.refresh_tree_from_text()
        self._render_preview()
        self._modified = False

    def get_file_path(self):
        return self._file_path

    def set_file_path(self, path):
        self._file_path = path

    def is_modified(self):
        return self._modified

    def set_modified(self, value):
        self._modified = value

    def set_role(self, role, lang=None):
        """Assign the semantic role (i18n / changelog / generic) and language."""
        self._role = role
        self._lang = lang
        self._rebuild_role_tools()

    def get_role(self):
        return self._role

    def get_lang(self):
        return self._lang

    def role_hint(self):
        if self._role in (ROLE_I18N, ROLE_CHANGELOG) and self._lang:
            return t("json.role.hint").format(role=role_label(self._role), lang=self._lang)
        return role_label(self._role)

    # ---------- Retranslate (live language switch) ----------
    def retranslate_ui(self):
        self.model.setHorizontalHeaderLabels(
            [t("json.col.key"), t("json.col.value"), t("json.col.type")]
        )
        self._a_refresh.setText(t("json.refresh"))
        self._a_apply.setText(t("json.apply"))
        self._a_format.setText(t("json.format"))
        self._a_minify.setText(t("json.minify"))
        self._a_validate.setText(t("json.validate"))
        self._a_expand.setText(t("json.expand"))
        self._a_collapse.setText(t("json.collapse"))
        self._auto_sync.setText(t("json.sync"))
        self._a_find.setText(t("json.find"))
        self._tools_btn.setText(t("json.tools"))
        self._a_preview.setText(t("json.edit") if self.right_stack.currentIndex() == 1 else t("json.preview"))
        self.text_edit.retranslate_ui()
        self._rebuild_role_tools()

    # ---------- Model building ----------
    @staticmethod
    def _type_name(value):
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, dict):
            return "object"
        if isinstance(value, list):
            return "array"
        if isinstance(value, str):
            return "string"
        if isinstance(value, (int, float)):
            return "number"
        if value is None:
            return "null"
        return "string"

    @staticmethod
    def _val_text(value):
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str):
            return value
        return str(value)

    def _lock(self, item):
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

    def _make_row(self, key, value):
        key_text = str(key) if key is not None else ""
        if isinstance(value, dict):
            key_item = QStandardItem(key_text or t("json.root.object"))
            val_item = QStandardItem("")
            type_item = QStandardItem("object")
            row = [key_item, val_item, type_item]
            for k, v in value.items():
                key_item.appendRow(self._make_row(k, v))
            self._lock(val_item)
            self._lock(type_item)
            return row
        if isinstance(value, list):
            key_item = QStandardItem(key_text or t("json.root.array"))
            val_item = QStandardItem("")
            type_item = QStandardItem("array")
            row = [key_item, val_item, type_item]
            for idx, v in enumerate(value):
                key_item.appendRow(self._make_row(str(idx), v))
            self._lock(val_item)
            self._lock(type_item)
            return row
        key_item = QStandardItem(key_text)
        val_item = QStandardItem(self._val_text(value))
        type_item = QStandardItem(self._type_name(value))
        self._lock(type_item)
        return [key_item, val_item, type_item]

    def _build_model(self, data):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(
            [t("json.col.key"), t("json.col.value"), t("json.col.type")]
        )
        self.model.appendRow(self._make_row(None, data))
        self.tree_view.expandToDepth(1)

    def _node_value(self, key_item):
        typ = key_item.text(2)
        if typ == "object":
            d = {}
            for r in range(key_item.rowCount()):
                child = key_item.child(r, 0)
                d[child.text(0)] = self._node_value(child)
            return d
        if typ == "array":
            arr = []
            for r in range(key_item.rowCount()):
                child = key_item.child(r, 0)
                arr.append(self._node_value(child))
            return arr
        return self._coerce(key_item.text(1), typ)

    @staticmethod
    def _coerce(raw, typ):
        if typ == "string":
            return raw
        if typ == "number":
            raw = (raw or "").strip()
            try:
                return int(raw)
            except ValueError:
                pass
            try:
                return float(raw)
            except ValueError:
                return 0
        if typ == "bool":
            return str(raw).strip().lower() in ("true", "1", "yes", "是")
        if typ == "null":
            return None
        return raw

    # ---------- Sync ----------
    def refresh_tree_from_text(self):
        text = self.text_edit.toPlainText()
        ok, err = is_valid_json(text)
        if not ok:
            self.message.emit(t("json.refresh.failed").format(err=err))
            return
        data = json.loads(text)
        self._loading = True
        self._build_model(data)
        self._loading = False
        self.message.emit(t("json.refresh"))

    def apply_tree_to_text(self):
        if self.model.rowCount() == 0:
            self._set_text("")
            return
        root = self.model.item(0, 0)
        try:
            data = self._node_value(root)
            text = json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, t("json.apply"), str(e))
            return
        self._set_text(text, mark_modified=True)
        self.message.emit(t("json.apply"))

    def _set_text(self, text, mark_modified=False):
        self._loading = True
        self.text_edit.setPlainText(text)
        self._loading = False
        self._modified = mark_modified
        if mark_modified:
            self.contentChanged.emit()

    # ---------- Format ----------
    def format_text(self):
        text = self.text_edit.toPlainText()
        ok, err = is_valid_json(text)
        if not ok:
            self.message.emit(t("json.format.failed").format(err=err))
            return
        self._set_text(pretty_json(text), mark_modified=True)
        self.refresh_tree_from_text()
        self.message.emit(t("json.format"))

    def minify_text(self):
        text = self.text_edit.toPlainText()
        ok, err = is_valid_json(text)
        if not ok:
            self.message.emit(t("json.minify.failed").format(err=err))
            return
        self._set_text(minify_json(text), mark_modified=True)
        self.message.emit(t("json.minify"))

    def validate(self):
        text = self.text_edit.toPlainText()
        ok, err = is_valid_json(text)
        if ok:
            self.message.emit(t("json.valid"))
        else:
            QMessageBox.warning(self, t("json.validate"), err)
            self.message.emit(t("json.invalid").format(err=err))

    def expand_all(self):
        self.tree_view.expandAll()

    def collapse_all(self):
        self.tree_view.collapseAll()

    # ---------- i18n role tools ----------
    def validate_schema(self):
        text = self.text_edit.toPlainText()
        ok, err = is_valid_json(text)
        if not ok:
            QMessageBox.warning(self, t("json.schema.check"), err)
            return
        issues = self._check_rich_text(json.loads(text), "")
        if not issues:
            QMessageBox.information(
                self, t("json.schema.check"),
                t("json.schema.ok").format(n=self._count_sections(json.loads(text))),
            )
            return
        msg = t("json.schema.error").format(n=len(issues)) + "\n" + "\n".join(
            t("json.schema.issue").format(path=p, msg=m) for p, m in issues[:50]
        )
        QMessageBox.warning(self, t("json.schema.check"), msg)

    def _count_sections(self, data):
        if isinstance(data, dict):
            return len(data)
        if isinstance(data, list):
            return len(data)
        return 1

    def _check_rich_text(self, node, path):
        issues = []
        if isinstance(node, dict):
            for k, v in node.items():
                issues.extend(self._check_rich_text(v, f"{path}.{k}" if path else k))
        elif isinstance(node, list):
            # A rich-text array: each item must be {type, content}.
            looks_rich = any(
                isinstance(x, dict) and ("content" in x or "type" in x) for x in node
            )
            if looks_rich:
                for i, item in enumerate(node):
                    ip = f"{path}[{i}]"
                    if not isinstance(item, dict):
                        issues.append((ip, "expected object {type, content}"))
                        continue
                    typ = item.get("type")
                    if typ not in _RICH_TYPES:
                        issues.append((ip, f"type must be one of {_RICH_TYPES}"))
                    if "content" not in item or not isinstance(item["content"], str):
                        issues.append((ip, "missing string 'content'"))
            else:
                for i, item in enumerate(node):
                    issues.extend(self._check_rich_text(item, f"{path}[{i}]"))
        return issues

    def _transform_rich(self, mode):
        """Wrap / unwrap / normalize rich-text fields across the document."""
        text = self.text_edit.toPlainText()
        ok, err = is_valid_json(text)
        if not ok:
            self.message.emit(t("json.transform.failed").format(err=err))
            return
        data = json.loads(text)
        count = 0
        if mode == "wrap":
            data, count = self._rich_wrap(data)
            msg = t("json.rich.wrapped").format(n=count)
        elif mode == "unwrap":
            data, count = self._rich_unwrap(data)
            msg = t("json.rich.unwrapped").format(n=count)
        else:  # normalize
            data, count = self._rich_normalize(data)
            msg = t("json.rich.normalized").format(n=count)
        if count == 0:
            self.message.emit(msg)
            return
        self._set_text(json.dumps(data, ensure_ascii=False, indent=2), mark_modified=True)
        self.refresh_tree_from_text()
        self.message.emit(msg)

    def _rich_wrap(self, node):
        """Wrap every string leaf into a single-item rich-text array."""
        count = 0
        if isinstance(node, dict):
            for k, v in list(node.items()):
                if isinstance(v, str):
                    node[k] = [{"type": "text", "content": v}]
                    count += 1
                else:
                    node[k], c = self._rich_wrap(v)
                    count += c
        elif isinstance(node, list):
            # Don't wrap inside an existing rich-text array.
            if node and all(isinstance(x, dict) and "content" in x for x in node):
                return node, count
            for i, v in enumerate(node):
                if isinstance(v, str):
                    node[i] = [{"type": "text", "content": v}]
                    count += 1
                else:
                    node[i], c = self._rich_wrap(v)
                    count += c
        return node, count

    def _rich_unwrap(self, node):
        """Flatten single-item rich-text arrays back to plain strings."""
        count = 0
        if isinstance(node, dict):
            for k, v in list(node.items()):
                if isinstance(v, list) and len(v) == 1 and isinstance(v[0], dict) and \
                        v[0].get("type") == "text" and "content" in v[0]:
                    node[k] = v[0]["content"]
                    count += 1
                else:
                    node[k], c = self._rich_unwrap(v)
                    count += c
        elif isinstance(node, list):
            for i, v in enumerate(node):
                if isinstance(v, list) and len(v) == 1 and isinstance(v[0], dict) and \
                        v[0].get("type") == "text" and "content" in v[0]:
                    node[i] = v[0]["content"]
                    count += 1
                else:
                    node[i], c = self._rich_unwrap(v)
                    count += c
        return node, count

    def _rich_normalize(self, node):
        """Ensure rich-text items have a valid type and string content."""
        count = 0
        if isinstance(node, dict):
            for k, v in list(node.items()):
                node[k], c = self._rich_normalize(v)
                count += c
        elif isinstance(node, list):
            if node and all(isinstance(x, dict) and "content" in x for x in node):
                for item in node:
                    if item.get("type") not in _RICH_TYPES:
                        item["type"] = "text"
                        count += 1
                    if not isinstance(item.get("content"), str):
                        item["content"] = str(item.get("content", ""))
                        count += 1
            else:
                for i, v in enumerate(node):
                    node[i], c = self._rich_normalize(v)
                    count += c
        return node, count

    # ---------- changelog role tools ----------
    def add_changelog_entry(self):
        text = self.text_edit.toPlainText()
        ok, err = is_valid_json(text)
        if not ok:
            QMessageBox.warning(self, t("json.add.entry"), err)
            return
        data = json.loads(text)
        if not isinstance(data, list):
            QMessageBox.warning(self, t("json.add.entry"), t("json.not.list"))
            return
        dlg = ChangelogEntryDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        entry = dlg.data()
        if not entry["version"]:
            QMessageBox.warning(self, t("json.add.entry"), t("json.entry.version"))
            return
        data.append(entry)
        self._set_text(json.dumps(data, ensure_ascii=False, indent=2), mark_modified=True)
        self.refresh_tree_from_text()
        self.message.emit(t("json.changelog.added").format(version=entry["version"]))

    # ---------- Preview ----------
    def toggle_preview(self):
        """Switch the right pane between the text editor and the rendered preview."""
        showing_preview = self.right_stack.currentIndex() == 0
        self.right_stack.setCurrentIndex(1 if showing_preview else 0)
        self._a_preview.setText(t("json.edit") if showing_preview else t("json.preview"))
        if showing_preview:
            self._render_preview()

    def _render_preview(self):
        text = self.text_edit.toPlainText()
        ok, _err = is_valid_json(text)
        if not ok:
            self.preview.show_invalid(get_preview_colors(), self._lang)
            return
        try:
            data = json.loads(text)
        except Exception:  # noqa: BLE001
            self.preview.show_invalid(get_preview_colors(), self._lang)
            return
        self.preview.render(data, self._role, self._lang, get_preview_colors())

    def retheme(self):
        """Re-apply theme colours to the code editor and preview."""
        self.text_edit.retheme()
        if self.right_stack.currentIndex() == 1:
            self._render_preview()

    # ---------- Events ----------
    def _on_text_changed(self):
        if self._loading:
            return
        self._modified = True
        self.contentChanged.emit()
        if self.right_stack.currentIndex() == 1:
            self._preview_timer.start()

    def _on_data_changed(self, *_):
        if self._loading or not self._auto_sync.isChecked():
            return
        self.apply_tree_to_text()

    # ---------- Context Menu ----------
    def _selected_key_item(self):
        index = self.tree_view.currentIndex()
        if not index.isValid():
            return None
        return self.model.itemFromIndex(index.siblingAtColumn(0))

    def _on_context_menu(self, pos):
        item = self._selected_key_item()
        menu = QMenu(self)
        if item is None:
            act = menu.addAction(t("json.add.child"))
            act.triggered.connect(lambda: self._add_child(None))
            menu.exec(self.tree_view.viewport().mapToGlobal(pos))
            return

        typ = item.text(2)
        if typ in ("object", "array"):
            menu.addAction(t("json.add.child"), lambda: self._add_child(item))
        parent = item.parent()
        if parent is not None:
            menu.addAction(t("json.add.sibling"), lambda: self._add_sibling(item))
            menu.addAction(t("json.delete"), lambda: self._delete(item))
        if typ in ("string", "number", "bool", "null"):
            sub = menu.addMenu(t("json.convert.type"))
            for ty in ("string", "number", "bool", "null"):
                sub.addAction(ty, lambda ty=ty: self._convert_type(item, ty))
        menu.exec(self.tree_view.viewport().mapToGlobal(pos))

    def _add_child(self, parent_item):
        if parent_item is None:
            if self.model.rowCount() == 0:
                self._build_model({})
            parent_item = self.model.item(0, 0)
        typ = parent_item.text(2)
        if typ == "array":
            key = str(parent_item.rowCount())
        else:
            key, ok = QInputDialog.getText(self, t("json.add.child"), t("json.col.key") + ":")
            if not ok or not key:
                key = t("json.newkey").format(n=parent_item.rowCount())
        row = [QStandardItem(key), QStandardItem(""), QStandardItem("string")]
        parent_item.appendRow(row)
        parent_item.setExpanded(True)
        if self._auto_sync.isChecked():
            self.apply_tree_to_text()

    def _add_sibling(self, item):
        parent = item.parent()
        if parent is None:
            return
        if parent.text(2) == "array":
            key = str(parent.rowCount())
        else:
            key, ok = QInputDialog.getText(self, t("json.add.sibling"), t("json.col.key") + ":")
            if not ok or not key:
                key = t("json.newkey").format(n=parent.rowCount())
        parent.appendRow([QStandardItem(key), QStandardItem(""), QStandardItem("string")])
        if self._auto_sync.isChecked():
            self.apply_tree_to_text()

    def _delete(self, item):
        parent = item.parent()
        if parent is None:
            QMessageBox.information(self, t("json.delete"), t("json.root.nodelete"))
            return
        parent.removeRow(item.row())
        if self._auto_sync.isChecked():
            self.apply_tree_to_text()

    def _convert_type(self, item, new_type):
        item.setText(2, new_type)
        defaults = {"string": "", "number": "0", "bool": "false", "null": "null"}
        item.setText(1, defaults[new_type])
        if self._auto_sync.isChecked():
            self.apply_tree_to_text()
