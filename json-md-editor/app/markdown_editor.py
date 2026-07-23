"""Markdown editor (role-aware: legal documents + generic markdown)."""

from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QListWidget,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.code_editor import CodeEditor
from app.file_role import ROLE_LEGAL, ROLE_GENERIC_MD, role_label
from app.i18n import t, LANG_DISPLAY, SUPPORTED_LANGS
from app.legal_features import (
    LEGAL_TEMPLATES,
    auto_number_articles,
    extract_headings,
    get_legal_template,
    word_count,
)
from app.markdown_converter import convert_markdown
from app.theme import get_preview_colors
from app.utils import write_text


from app.fonts import css_font_stack
from app.i18n import get_lang


def _preview_css(colors, lang=None):
    return f"""
<style>
  body {{ background:{colors['bg']}; color:{colors['text']}; font-family:{css_font_stack(lang)}; line-height:1.75; padding:20px 26px; }}
  h1,h2,h3,h4 {{ color:{colors['accent']}; border-bottom:1px solid {colors['border']}; padding-bottom:6px; margin-top:1.4em; }}
  h1 {{ font-size:1.7em; }} h2 {{ font-size:1.35em; }} h3 {{ font-size:1.15em; }}
  code {{ background:{colors['code_bg']}; padding:2px 6px; border-radius:5px; font-family:Consolas,monospace; }}
  pre {{ background:{colors['code_bg']}; padding:14px; border-radius:8px; overflow:auto; border:1px solid {colors['border']}; }}
  pre code {{ background:none; padding:0; }}
  blockquote {{ border-left:4px solid {colors['accent']}; margin:0; padding:6px 16px; color:{colors['muted']}; background:{colors['section_bg']}; border-radius:0 8px 8px 0; }}
  table {{ border-collapse:collapse; width:100%; }}
  th,td {{ border:1px solid {colors['border']}; padding:7px 11px; }}
  th {{ background:{colors['code_bg']}; color:{colors['accent']}; }}
  a {{ color:{colors['link']}; }}
  hr {{ border:none; border-top:1px solid {colors['border']}; }}
  ul,ol {{ padding-left:1.4em; }}
</style>
"""


class MarkdownEditor(QWidget):
    contentChanged = pyqtSignal()
    message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._file_path = None
        self._modified = False
        self._role = ROLE_GENERIC_MD
        self._lang = None

        self.editor = CodeEditor(mode="markdown")
        self.editor.textChanged.connect(self._on_text_changed)

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        self.splitter.setSizes([500, 500])

        self.toolbar = QToolBar()
        self._build_toolbar()

        self.find_widget = self.editor.find_widget

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.find_widget)
        layout.addWidget(self.splitter, 1)

        self._timer = QTimer()
        self._timer.setInterval(300)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._render_preview)

        QShortcut(QKeySequence.StandardKey.Find, self, self.editor.toggle_find)
        self._render_preview()

    # ---------- Toolbar ----------
    def _build_toolbar(self):
        tb = self.toolbar
        self._preview_btn = tb.addAction(t("md.hide.preview"), self._toggle_preview)
        tb.addSeparator()
        self._a_export_html = tb.addAction(t("md.export.html"), self.export_html)
        self._a_export_pdf = tb.addAction(t("md.export.pdf"), self.export_pdf)
        tb.addSeparator()
        # Template dropdown
        self._tpl_btn = QToolButton()
        self._tpl_btn.setText(t("md.insert.template"))
        self._tpl_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._tpl_menu = QMenu(self._tpl_btn)
        self._tpl_btn.setMenu(self._tpl_menu)
        tb.addWidget(self._tpl_btn)
        tb.addSeparator()
        self._a_auto_num = tb.addAction(t("md.auto.number"), self.auto_number)
        self._a_toc = tb.addAction(t("md.toc"), self.show_toc)
        self._a_stats = tb.addAction(t("md.word.count"), self.show_stats)
        tb.addSeparator()
        self._a_find = tb.addAction(t("md.word.count"), self.editor.toggle_find)
        self._a_find.setText(t("json.find"))
        self._rebuild_template_menu()

    def _rebuild_template_menu(self):
        menu = self._tpl_menu
        menu.clear()
        if self._role == ROLE_LEGAL:
            for lang in SUPPORTED_LANGS:
                label = t("md.lang.template").format(lang=LANG_DISPLAY.get(lang, lang))
                menu.addAction(label, lambda l=lang: self._insert_lang_template(l))
        else:
            for name in LEGAL_TEMPLATES:
                menu.addAction(name, lambda n=name: self._insert_generic_template(n))

    def _insert_lang_template(self, lang):
        text = get_legal_template(lang).format(date="____")
        self.editor.insertPlainText(text)
        self.editor.setFocus()
        self.message.emit(t("md.lang.template").format(lang=LANG_DISPLAY.get(lang, lang)))

    def _insert_generic_template(self, name):
        text = LEGAL_TEMPLATES[name].format(date="____")
        self.editor.insertPlainText(text)
        self.editor.setFocus()
        self.message.emit(t("md.template.inserted").format(name=name))

    # ---------- External Interfaces ----------
    def get_text(self):
        return self.editor.toPlainText()

    def set_text(self, text, mark_modified=False):
        self.editor.setPlainText(text)
        self._modified = mark_modified

    def load_file(self, path, text):
        self._file_path = path
        self.set_text(text, mark_modified=False)
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
        self._role = role
        self._lang = lang
        self._rebuild_template_menu()

    def get_role(self):
        return self._role

    def get_lang(self):
        return self._lang

    def role_hint(self):
        if self._role == ROLE_LEGAL and self._lang:
            return t("json.role.hint").format(role=role_label(self._role), lang=self._lang)
        return role_label(self._role)

    # ---------- Retranslate (live language switch) ----------
    def retranslate_ui(self):
        self._preview_btn.setText(
            t("md.hide.preview") if self.preview.isVisible() else t("md.show.preview")
        )
        self._a_export_html.setText(t("md.export.html"))
        self._a_export_pdf.setText(t("md.export.pdf"))
        self._tpl_btn.setText(t("md.insert.template"))
        self._a_auto_num.setText(t("md.auto.number"))
        self._a_toc.setText(t("md.toc"))
        self._a_stats.setText(t("md.word.count"))
        self._a_find.setText(t("json.find"))
        self.editor.retranslate_ui()
        self._rebuild_template_menu()

    # ---------- Preview ----------
    def _render_preview(self):
        text = self.editor.toPlainText()
        body = convert_markdown(text)
        self.preview.setHtml(_preview_css(get_preview_colors(), self._lang) + body)

    def retheme(self):
        """Re-apply theme colours to the code editor and re-render preview."""
        self.editor.retheme()
        self._render_preview()

    def _schedule_render(self):
        self._timer.start()

    def _toggle_preview(self):
        if self.preview.isVisible():
            self.preview.hide()
            self._preview_btn.setText(t("md.show.preview"))
        else:
            self.preview.show()
            self._preview_btn.setText(t("md.hide.preview"))
            self._render_preview()

    # ---------- Template / Number / Contents / Word Count ----------
    def auto_number(self):
        # Site privacy docs use "##" for articles -> article_level=2.
        article_level = 2 if self._role == ROLE_LEGAL else 1
        new_text = auto_number_articles(self.editor.toPlainText(), lang=self._lang,
                                         article_level=article_level)
        self.editor.setPlainText(new_text)
        self.message.emit(t("md.auto.number"))

    def show_toc(self):
        headings = extract_headings(self.editor.toPlainText())
        if not headings:
            QMessageBox.information(self, t("md.toc.title"), t("md.toc.none"))
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(t("md.toc.title"))
        dlg.resize(420, 480)
        lst = QListWidget()
        for line, level, title in headings:
            indent = "    " * (level - 1)
            lst.addItem(f"{indent}{'#' * level} {title}")
        lst.itemDoubleClicked.connect(
            lambda _item: self._jump_to_line(headings[lst.row(_item)][0], dlg)
        )
        lay = QVBoxLayout(dlg)
        lay.addWidget(lst)
        dlg.setLayout(lay)
        dlg.exec()

    def _jump_to_line(self, line, dlg):
        cursor = self.editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        for _ in range(line):
            cursor.movePosition(cursor.MoveOperation.Down)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()
        dlg.accept()

    def show_stats(self):
        stats = word_count(self.editor.toPlainText())
        QMessageBox.information(
            self, t("md.stats.title"),
            t("md.stats.body").format(
                chars=stats["chars"], cjk=stats["cjk"], words=stats["words"],
                lines=stats["lines"], pages=stats["pages"],
            ),
        )

    # ---------- Export ----------
    def export_html(self):
        path, _ = QFileDialog.getSaveFileName(
            self, t("md.export.html.title"), "document.html", "HTML File (*.html)"
        )
        if not path:
            return
        body = convert_markdown(self.editor.toPlainText())
        html = (
            "<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'>"
            "<title>Export Document</title>" + _preview_css(get_preview_colors(), self._lang) + "</head><body>"
            + body + "</body></html>"
        )
        write_text(path, html)
        self.message.emit(f"{t('md.export.html')}: {path}")

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, t("md.export.pdf.title"), "document.pdf", "PDF File (*.pdf)"
        )
        if not path:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        if QPrintDialog(printer, self).exec() == QDialog.DialogCode.Accepted:
            self.preview.print_(printer)
            self.message.emit(f"{t('md.export.pdf')}: {path}")

    # ---------- Events ----------
    def _on_text_changed(self):
        self._modified = True
        self.contentChanged.emit()
        self._schedule_render()
