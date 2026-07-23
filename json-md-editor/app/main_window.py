"""Main window.

Wires together the JSON / Markdown editors, file explorer, a live language
selector (ja / en / zh-Hans / zh-TW), project-aware file roles, and the
cross-language consistency checker for the self-info site data.
"""

import json
import os

from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QCloseEvent, QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.file_explorer import FileExplorer
from app.file_role import detect_role
from app.fonts import build_font_families
from app.i18n import (
    SUPPORTED_LANGS,
    LANG_DISPLAY,
    get_lang,
    set_lang,
    t,
)
from app.json_editor import JsonEditor
from app.markdown_editor import MarkdownEditor
from app.theme import apply_theme
from app.utils import detect_file_type, human_size, read_text, write_text


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._settings = QSettings("self-info", "JsonMdEditor")
        saved_lang = self._settings.value("language", get_lang())
        set_lang(saved_lang)
        self._apply_font()

        self.setWindowTitle(t("app.title"))
        self.resize(1240, 820)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.setElideMode(Qt.TextElideMode.ElideRight)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        central = QWidget()
        central.setObjectName("central")
        central.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(10, 8, 10, 6)
        central_layout.addWidget(self.tabs)
        self.setCentralWidget(central)

        # File explorer
        self.explorer = FileExplorer()
        self.explorer.fileOpened.connect(self.open_file)
        dock = QDockWidget(t("view.toggle.explorer"), self)
        dock.setWidget(self.explorer)
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        self._explorer_dock = dock

        self._build_menu()
        self._build_toolbar()
        self._build_statusbar()
        self._bind_shortcuts()

        # Apply persisted theme (System / Light / Dark) and follow OS live.
        saved_theme = self._settings.value("theme", "system")
        idx = self._theme_combo.findData(saved_theme)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)
        self._apply_current_theme()
        app = QApplication.instance()
        if app is not None:
            try:
                app.styleHints().colorSchemeChanged.connect(self._on_system_scheme_changed)
            except Exception:  # noqa: BLE001
                pass

    # ---------- Menu / Toolbar ----------
    def _build_menu(self):
        menubar = self.menuBar()
        self._menu_file = menubar.addMenu(t("menu.file"))
        self._a_new_json = self._menu_file.addAction(t("file.new") + " JSON", lambda: self.new_file("json"))
        self._a_new_json.setShortcut(QKeySequence.StandardKey.New)
        self._a_new_md = self._menu_file.addAction(t("file.new") + " MD", lambda: self.new_file("markdown"))
        self._menu_file.addSeparator()
        self._a_open = self._menu_file.addAction(t("file.open"), self.open_dialog)
        self._a_open.setShortcut(QKeySequence.StandardKey.Open)
        self._a_open_folder = self._menu_file.addAction(t("file.open.folder"), self.explorer._choose_folder)
        self._menu_file.addSeparator()
        self._a_save = self._menu_file.addAction(t("file.save"), self.save_current)
        self._a_save.setShortcut(QKeySequence.StandardKey.Save)
        self._a_save_as = self._menu_file.addAction(t("file.save.as"), self.save_as)
        self._a_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        self._menu_file.addSeparator()
        self._a_close_tab = self._menu_file.addAction(t("file.close"), self._close_current)
        self._a_close_tab.setShortcut(QKeySequence.StandardKey.Close)
        self._menu_file.addSeparator()
        self._a_quit = self._menu_file.addAction(t("file.exit"), self.close)
        self._a_quit.setShortcut(QKeySequence.StandardKey.Quit)

        self._menu_edit = menubar.addMenu(t("menu.edit"))
        self._a_find = self._menu_edit.addAction(t("edit.find"), self._find_in_current)
        self._a_find.setShortcut(QKeySequence.StandardKey.Find)

        self._menu_view = menubar.addMenu(t("menu.view"))
        self._view_toggle = self._explorer_dock.toggleViewAction()
        self._view_toggle.setText(t("view.toggle.explorer"))
        self._menu_view.addAction(self._view_toggle)

        self._menu_tools = menubar.addMenu(t("menu.tools"))
        self._a_consistency = self._menu_tools.addAction(t("tools.consistency"), self._run_consistency)

        self._menu_help = menubar.addMenu(t("menu.help"))
        self._a_about = self._menu_help.addAction(t("help.about"), self._about)

    def _build_toolbar(self):
        tb = QToolBar()
        self.addToolBar(tb)
        self._tb_new_json = tb.addAction(t("file.new") + " JSON", lambda: self.new_file("json"))
        self._tb_new_md = tb.addAction(t("file.new") + " MD", lambda: self.new_file("markdown"))
        self._tb_open = tb.addAction(t("file.open"), self.open_dialog)
        self._tb_save = tb.addAction(t("file.save"), self.save_current)
        tb.addSeparator()
        self._tb_find = tb.addAction(t("edit.find"), self._find_in_current)
        tb.addSeparator()
        # Live language selector
        lang_label = QLabel(t("lang.label") + ":")
        tb.addWidget(lang_label)
        self._lang_combo = QComboBox()
        for lang in SUPPORTED_LANGS:
            self._lang_combo.addItem(LANG_DISPLAY[lang], lang)
        self._lang_combo.setCurrentText(LANG_DISPLAY.get(get_lang(), "简体中文"))
        self._lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        tb.addWidget(self._lang_combo)
        tb.addSeparator()
        # Live theme selector (System / Light / Dark)
        theme_label = QLabel(t("theme.label") + ":")
        self._theme_label = theme_label
        tb.addWidget(theme_label)
        self._theme_combo = QComboBox()
        for mode in ("system", "light", "dark"):
            self._theme_combo.addItem(t("theme." + mode), mode)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        tb.addWidget(self._theme_combo)

    def _build_statusbar(self):
        self.statusBar().showMessage(t("app.subtitle"))
        self._file_label = QLabel()
        self._cursor_label = QLabel()
        self.statusBar().addPermanentWidget(self._file_label)
        self.statusBar().addPermanentWidget(self._cursor_label)

    def _bind_shortcuts(self):
        for seq, fn in [
            (QKeySequence.StandardKey.New, lambda: self.new_file("json")),
            (QKeySequence.StandardKey.Open, self.open_dialog),
            (QKeySequence.StandardKey.Save, self.save_current),
            (QKeySequence.StandardKey.SaveAs, self.save_as),
            (QKeySequence.StandardKey.Close, self._close_current),
            (QKeySequence.StandardKey.Find, self._find_in_current),
        ]:
            QShortcut(seq, self, fn)

    # ---------- Language switching ----------
    def _apply_font(self):
        """Apply the per-locale custom font (matches the self-info site)."""
        font = QFont()
        font.setFamilies(build_font_families(get_lang()))
        font.setPointSize(10)
        app = QApplication.instance()
        if app is not None:
            app.setFont(font)

    def _on_lang_changed(self, _index):
        lang = self._lang_combo.currentData()
        if not lang:
            return
        set_lang(lang)
        self._settings.setValue("language", lang)
        self._apply_font()
        # Re-apply the theme so the QSS font-family (injected per language)
        # switches to the new locale's webfont (LXGW WenKai GB/TC, Klee One).
        self._apply_current_theme()
        self.retranslate_ui()
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if hasattr(w, "retranslate_ui"):
                w.retranslate_ui()
        self._update_info()
        self._update_cursor_status()

    # ---------- Theme switching ----------
    def _on_theme_changed(self, _index):
        mode = self._theme_combo.currentData()
        if not mode:
            return
        self._settings.setValue("theme", mode)
        self._apply_current_theme()

    def _apply_current_theme(self):
        mode = self._theme_combo.currentData() or "system"
        apply_theme(QApplication.instance() or self, get_lang(), mode)
        # Aggressive full-window style refresh.  On Windows, QDockWidget and
        # QMenuBar/QToolBar cache native colours that survive a simple
        # setStyleSheet().  Unpolish + polish the entire widget tree.
        app = QApplication.instance()
        if app is not None:
            style = app.style()
            # Refresh the main window and every direct child.
            for target in (self, self._explorer_dock, self.explorer,
                           self.menuBar(), self.statusBar()):
                style.unpolish(target)
                style.polish(target)
            # Also refresh all toolbars.
            for tb in self.findChildren(QToolBar):
                style.unpolish(tb)
                style.polish(tb)
        # Editor-level retheme (gutter / syntax highlighter).
        if hasattr(self.explorer, "retheme"):
            self.explorer.retheme()
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if hasattr(w, "retheme"):
                w.retheme()

    def _on_system_scheme_changed(self):
        # Live-follow the OS colour scheme only while in "system" mode.
        if self._theme_combo.currentData() == "system":
            self._apply_current_theme()

    def retranslate_ui(self):
        self.setWindowTitle(t("app.title"))
        self._theme_label.setText(t("theme.label") + ":")
        for i in range(self._theme_combo.count()):
            self._theme_combo.setItemText(i, t("theme." + self._theme_combo.itemData(i)))
        self._menu_file.setTitle(t("menu.file"))
        self._a_new_json.setText(t("file.new") + " JSON")
        self._a_new_md.setText(t("file.new") + " MD")
        self._a_open.setText(t("file.open"))
        self._a_open_folder.setText(t("file.open.folder"))
        self._a_save.setText(t("file.save"))
        self._a_save_as.setText(t("file.save.as"))
        self._a_close_tab.setText(t("file.close"))
        self._a_quit.setText(t("file.exit"))
        self._menu_edit.setTitle(t("menu.edit"))
        self._a_find.setText(t("edit.find"))
        self._menu_view.setTitle(t("menu.view"))
        self._view_toggle.setText(t("view.toggle.explorer"))
        self._menu_tools.setTitle(t("menu.tools"))
        self._a_consistency.setText(t("tools.consistency"))
        self._menu_help.setTitle(t("menu.help"))
        self._a_about.setText(t("help.about"))
        self._tb_new_json.setText(t("file.new") + " JSON")
        self._tb_new_md.setText(t("file.new") + " MD")
        self._tb_open.setText(t("file.open"))
        self._tb_save.setText(t("file.save"))
        self._tb_find.setText(t("edit.find"))
        self._explorer_dock.setWindowTitle(t("view.toggle.explorer"))
        if hasattr(self.explorer, "retranslate_ui"):
            self.explorer.retranslate_ui()
        self.statusBar().showMessage(t("app.subtitle"))

    # ---------- File operations ----------
    def new_file(self, ftype):
        if ftype == "json":
            editor = JsonEditor()
            editor.set_text("{\n  \n}", mark_modified=False)
            title = "Untitled.json"
        else:
            editor = MarkdownEditor()
            editor.set_text("", mark_modified=False)
            title = "Untitled.md"
        self._add_editor(editor, ftype, title, None)

    def open_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, t("dlg.open.title"), os.getcwd(),
            f"{t('dlg.filter.json')};;{t('dlg.filter.md')};;{t('dlg.filter.all')}",
        )
        if path:
            self.open_file(path)

    def open_file(self, path):
        existing = self._find_tab_by_path(path)
        if existing is not None:
            self.tabs.setCurrentIndex(existing)
            return
        ftype = detect_file_type(path)
        if ftype == "unknown":
            QMessageBox.warning(self, t("app.title"), t("file.unsupported").format(path=path))
            return
        try:
            text = read_text(path)
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, t("file.read.failed"), str(e))
            return
        role, lang = detect_role(path)
        if ftype == "json":
            editor = JsonEditor()
        else:
            editor = MarkdownEditor()
        editor.load_file(path, text)
        editor.set_role(role, lang)
        self._add_editor(editor, ftype, os.path.basename(path), path)

    def _add_editor(self, editor, ftype, title, path):
        editor._file_type = ftype
        idx = self.tabs.addTab(editor, title)
        self.tabs.setCurrentIndex(idx)
        editor.contentChanged.connect(lambda: self._on_content_changed(idx))
        editor.message.connect(self.statusBar().showMessage)
        inner = editor.text_edit if ftype == "json" else editor.editor
        inner.cursorPositionChanged.connect(self._update_cursor_status)
        if path is None:
            editor.set_file_path(None)
        self._update_cursor_status()
        self._update_info()

    def _find_tab_by_path(self, path):
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if w.get_file_path() == path:
                return i
        return None

    def save_current(self):
        idx = self.tabs.currentIndex()
        if idx < 0:
            return
        editor = self.tabs.widget(idx)
        path = editor.get_file_path()
        if path is None:
            path, _ = QFileDialog.getSaveFileName(
                self, t("dlg.save.title"),
                f"Untitled.{editor._file_type}",
                "JSON (*.json)" if editor._file_type == "json" else "Markdown (*.md)",
            )
            if not path:
                return
        try:
            write_text(path, editor.get_text())
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, t("file.save.failed"), str(e))
            return
        editor.set_file_path(path)
        editor.set_modified(False)
        self.tabs.setTabText(idx, os.path.basename(path))
        self.statusBar().showMessage(f"{t('file.save')}: {path}")
        self._update_info()

    def save_as(self):
        idx = self.tabs.currentIndex()
        if idx < 0:
            return
        editor = self.tabs.widget(idx)
        path, _ = QFileDialog.getSaveFileName(
            self, t("dlg.save.title"),
            editor.get_file_path() or f"Untitled.{editor._file_type}",
            "JSON (*.json)" if editor._file_type == "json" else "Markdown (*.md)",
        )
        if not path:
            return
        try:
            write_text(path, editor.get_text())
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, t("file.save.failed"), str(e))
            return
        editor.set_file_path(path)
        editor.set_modified(False)
        self.tabs.setTabText(idx, os.path.basename(path))
        self.statusBar().showMessage(f"{t('file.save')}: {path}")

    def close_tab(self, idx):
        editor = self.tabs.widget(idx)
        if editor is None:
            return
        if editor.is_modified():
            r = QMessageBox.question(
                self, t("dlg.unsaved.title"),
                t("dlg.unsaved.msg").format(name=self.tabs.tabText(idx)),
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if r == QMessageBox.StandardButton.Cancel:
                return
            if r == QMessageBox.StandardButton.Save:
                self.tabs.setCurrentIndex(idx)
                self.save_current()
        self.tabs.removeTab(idx)

    def _close_current(self):
        if self.tabs.currentIndex() >= 0:
            self.close_tab(self.tabs.currentIndex())

    # ---------- Status Update ----------
    def _on_content_changed(self, idx):
        editor = self.tabs.widget(idx)
        if editor is None:
            return
        title = self.tabs.tabText(idx)
        if editor.is_modified() and not title.endswith(" *"):
            self.tabs.setTabText(idx, title + " *")
        elif not editor.is_modified() and title.endswith(" *"):
            self.tabs.setTabText(idx, title[:-2])
        self._update_info()

    def _update_cursor_status(self):
        editor = self.tabs.currentWidget()
        if editor is None:
            self._cursor_label.setText("")
            return
        inner = editor.text_edit if editor._file_type == "json" else editor.editor
        cursor = inner.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.positionInBlock() + 1
        self._cursor_label.setText(t("status.line.col").format(line=line, col=col))

    def _update_info(self):
        editor = self.tabs.currentWidget()
        if editor is None:
            self._file_label.setText("")
            return
        text = editor.get_text()
        size = human_size(len(text.encode("utf-8")))
        hint = editor.role_hint() if hasattr(editor, "role_hint") else editor._file_type.upper()
        self._file_label.setText(f"{hint}   |   {size}")

    def _on_tab_changed(self, _):
        self._update_cursor_status()
        self._update_info()

    def _find_in_current(self):
        editor = self.tabs.currentWidget()
        if editor is not None:
            if editor._file_type == "json":
                editor.text_edit.toggle_find()
            else:
                editor.editor.toggle_find()

    # ---------- Cross-language consistency ----------
    def _run_consistency(self):
        folder = QFileDialog.getExistingDirectory(
            self, t("consistency.pick.folder"), os.getcwd()
        )
        if not folder:
            return
        i18n_dir = os.path.join(folder, "i18n")
        files = {}
        for lang in SUPPORTED_LANGS:
            p = os.path.join(i18n_dir, lang + ".json")
            if os.path.exists(p):
                try:
                    with open(p, encoding="utf-8") as fh:
                        files[lang] = json.load(fh)
                except Exception as e:  # noqa: BLE001
                    QMessageBox.warning(self, t("consistency.title"), str(e))
                    return
        if not files:
            QMessageBox.warning(self, t("consistency.title"), t("consistency.not.found"))
            return
        all_keys = set()
        for d in files.values():
            if isinstance(d, dict):
                all_keys |= set(d.keys())
        report = []
        for lang, d in files.items():
            if not isinstance(d, dict):
                continue
            missing = all_keys - set(d.keys())
            if missing:
                report.append(
                    t("consistency.missing.keys").format(
                        lang=LANG_DISPLAY[lang], keys=", ".join(sorted(missing))
                    )
                )
        if report:
            QMessageBox.warning(self, t("consistency.title"), "\n".join(report))
        else:
            n = len(next(iter(files.values()))) if files else 0
            QMessageBox.information(self, t("consistency.title"), t("consistency.ok").format(n=n))

    # ---------- About ----------
    def _about(self):
        QMessageBox.about(self, t("dlg.about.title"), t("dlg.about.text"))

    def closeEvent(self, event: QCloseEvent):
        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            if editor.is_modified():
                self.tabs.setCurrentIndex(i)
                r = QMessageBox.question(
                    self, t("dlg.unsaved.title"),
                    t("dlg.unsaved.msg").format(name=self.tabs.tabText(i)),
                    QMessageBox.StandardButton.Save
                    | QMessageBox.StandardButton.Discard
                    | QMessageBox.StandardButton.Cancel,
                )
                if r == QMessageBox.StandardButton.Cancel:
                    event.ignore()
                    return
                if r == QMessageBox.StandardButton.Save:
                    self.save_current()
        event.accept()
