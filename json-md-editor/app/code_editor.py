"""Plain text code editor with line numbers, find bar, and zoom support."""

from PyQt6.QtCore import Qt, QEvent, QRect, QSize, QTimer
from PyQt6.QtGui import QColor, QFont, QKeySequence, QPainter, QTextBlock, QTextCursor, QTextDocument, QTextFormat
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QWidget,
)

from app.highlighters import JsonHighlighter, MarkdownHighlighter
from app.i18n import t
from app.theme import get_editor_colors


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return QSize(self._editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self._editor.lineNumberAreaPaintEvent(event)


class FindWidget(QWidget):
    """Find bar widget attached to the editor top."""

    def __init__(self, target, parent=None):
        super().__init__(parent)
        self._target = target
        self._case = False
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._edit = QLineEdit()
        self._edit.returnPressed.connect(lambda: self._do_find(False))
        layout.addWidget(self._edit)

        self._btn_prev = QPushButton()
        self._btn_prev.clicked.connect(lambda: self._do_find(True))
        self._btn_next = QPushButton()
        self._btn_next.clicked.connect(lambda: self._do_find(False))
        self._case_btn = QPushButton("Aa")
        self._case_btn.setCheckable(True)
        self._case_btn.toggled.connect(self._on_case)
        self._btn_close = QPushButton("✕")
        self._btn_close.setFixedWidth(30)
        self._btn_close.clicked.connect(self.hide)
        layout.addWidget(self._btn_prev)
        layout.addWidget(self._btn_next)
        layout.addWidget(self._case_btn)
        layout.addWidget(self._btn_close)
        self.retranslate_ui()

    def retranslate_ui(self):
        self._edit.setPlaceholderText(t("find.placeholder"))
        self._btn_prev.setText("↑ " + t("find.prev"))
        self._btn_next.setText("↓ " + t("find.next"))
        self._case_btn.setToolTip(t("find.case.tip"))
        self._btn_close.setToolTip(t("find.close.tip"))

    def _on_case(self, checked):
        self._case = checked

    def showEvent(self, event):
        self._edit.setFocus()
        self._edit.selectAll()
        super().showEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self._target.setFocus()
        else:
            super().keyPressEvent(event)

    def _do_find(self, backward):
        text = self._edit.text()
        if not text:
            return
        flags = QTextDocument.FindFlag(0)
        if self._case:
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if backward:
            flags |= QTextDocument.FindFlag.FindBackward
        if not self._target.find(text, flags):
            # Wrap around find
            cursor = self._target.textCursor()
            if backward:
                cursor.movePosition(QTextCursor.MoveOperation.End)
            else:
                cursor.movePosition(QTextCursor.MoveOperation.Start)
            self._target.setTextCursor(cursor)
            self._target.find(text, flags)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None, mode="text"):
        super().__init__(parent)
        self.setObjectName("codeEditor")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._mode = mode
        self._colors = get_editor_colors()
        self._line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)

        font = QFont()
        font.setFamilies(["Cascadia Code", "Consolas", "Menlo", "Monaco", "Courier New", "monospace"])
        font.setPointSize(11)
        self.setFont(font)

        self._highlighter = None
        self.set_mode(mode)

        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._apply_tab_width()

        self.find_widget = FindWidget(self)
        self.find_widget.hide()

    # ---- Line number area ----
    def lineNumberAreaWidth(self):
        digits = max(1, len(str(self.blockCount())))
        return 6 + self.fontMetrics().horizontalAdvance("9") * digits

    def updateLineNumberAreaWidth(self, _=0):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height())
        )

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor(self._colors["gutter_bg"]))
        current_block = self.textCursor().blockNumber()
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                num = str(block_number + 1)
                if block_number == current_block:
                    painter.setPen(QColor(self._colors["gutter_fg_current"]))
                else:
                    painter.setPen(QColor(self._colors["gutter_fg"]))
                painter.drawText(
                    0,
                    top,
                    self._line_number_area.width() - 4,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    num,
                )
            block = block.next()
            top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlightCurrentLine(self):
        extra = []
        if not self.isReadOnly():
            sel = QTextEdit_ExtraSelection()
            sel.format.setBackground(QColor(self._colors["current_line"]))
            sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            extra.append(sel)
        self.setExtraSelections(extra)
        # Repaint the gutter so the current-line number colour updates too.
        self._line_number_area.update()

    def retheme(self):
        """Re-apply theme colours to the gutter, current line, and syntax."""
        self._colors = get_editor_colors()
        if self._highlighter is not None and hasattr(self._highlighter, "apply_theme"):
            self._highlighter.apply_theme()
        self.highlightCurrentLine()
        self._line_number_area.update()
        self.viewport().update()

    def retranslate_ui(self):
        self.find_widget.retranslate_ui()

    # ---- Zoom ----
    def zoom_in(self):
        self._zoom(1)

    def zoom_out(self):
        self._zoom(-1)

    def _zoom(self, step):
        font = self.font()
        size = font.pointSize() + step
        size = max(8, min(42, size))
        font.setPointSize(size)
        self.setFont(font)
        self._apply_tab_width()
        self.updateLineNumberAreaWidth(0)

    def _apply_tab_width(self):
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(" "))

    # ---- Mode / Highlighting ----
    def set_mode(self, mode):
        if mode == self._mode and self._highlighter is not None:
            return
        self._mode = mode
        if self._highlighter is not None:
            self._highlighter.setDocument(None)
            self._highlighter = None
        if mode == "json":
            self._highlighter = JsonHighlighter(self.document())
        elif mode == "markdown":
            self._highlighter = MarkdownHighlighter(self.document())

    def toggle_find(self):
        if self.find_widget.isVisible():
            self.find_widget.hide()
            self.setFocus()
        else:
            self.find_widget.show()
            self.find_widget._edit.setFocus()
            self.find_widget._edit.selectAll()


# QPlainTextEdit extra selection structure reused from QTextEdit.ExtraSelection
from PyQt6.QtWidgets import QTextEdit  # noqa: E402

QTextEdit_ExtraSelection = QTextEdit.ExtraSelection
