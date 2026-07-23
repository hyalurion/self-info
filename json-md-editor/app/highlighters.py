"""Syntax highlighters for JSON and Markdown (theme-aware)."""

from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat

from app.theme import get_editor_colors


class JsonHighlighter(QSyntaxHighlighter):
    """Highlighter for JSON text. Colours follow the active theme."""

    def __init__(self, document):
        super().__init__(document)
        self.rules = []
        self.apply_theme()

    def apply_theme(self, colors=None):
        c = colors or get_editor_colors()
        self.rules = []

        # string
        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor(c["str"]))
        self.rules.append((QRegularExpression(r'"(?:\\.|[^"\\])*"'), str_fmt))

        # number
        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor(c["num"]))
        self.rules.append(
            (QRegularExpression(r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'), num_fmt)
        )

        # boolean / null
        kw_fmt = QTextCharFormat()
        kw_fmt.setForeground(QColor(c["kw"]))
        self.rules.append(
            (QRegularExpression(r'\b(?:true|false|null)\b'), kw_fmt)
        )

        # key (string followed by colon), placed last to override string colour
        key_fmt = QTextCharFormat()
        key_fmt.setForeground(QColor(c["key"]))
        key_fmt.setFontWeight(QFont.Weight.Bold)
        self.rules.append(
            (QRegularExpression(r'"(?:\\.|[^"\\])*"\s*(?=:)'), key_fmt)
        )
        self.rehighlight()

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


class MarkdownHighlighter(QSyntaxHighlighter):
    """Highlighter for Markdown text. Colours follow the active theme."""

    def __init__(self, document):
        super().__init__(document)
        self.rules = []
        self.apply_theme()

    def apply_theme(self, colors=None):
        c = colors or get_editor_colors()
        self.rules = []

        # heading
        h_fmt = QTextCharFormat()
        h_fmt.setForeground(QColor(c["heading"]))
        h_fmt.setFontWeight(QFont.Weight.Bold)
        self.rules.append((QRegularExpression(r'^#{1,6}\s.*$'), h_fmt))

        # bold
        bold_fmt = QTextCharFormat()
        bold_fmt.setForeground(QColor(c["bold"]))
        bold_fmt.setFontWeight(QFont.Weight.Bold)
        self.rules.append((QRegularExpression(r'\*\*.+?\*\*'), bold_fmt))
        self.rules.append((QRegularExpression(r'__.+?__'), bold_fmt))

        # italic
        ital_fmt = QTextCharFormat()
        ital_fmt.setForeground(QColor(c["italic"]))
        ital_fmt.setFontItalic(True)
        self.rules.append((QRegularExpression(r'\*[^*]+\*'), ital_fmt))
        self.rules.append((QRegularExpression(r'_[^_]+_'), ital_fmt))

        # inline code
        code_fmt = QTextCharFormat()
        code_fmt.setForeground(QColor(c["code"]))
        code_fmt.setFontFamily("Consolas")
        self.rules.append((QRegularExpression(r'`[^`]+`'), code_fmt))

        # list marker
        list_fmt = QTextCharFormat()
        list_fmt.setForeground(QColor(c["list"]))
        self.rules.append((QRegularExpression(r'^\s*([-*+]|\d+\.)\s'), list_fmt))

        # blockquote
        bq_fmt = QTextCharFormat()
        bq_fmt.setForeground(QColor(c["quote"]))
        bq_fmt.setFontItalic(True)
        self.rules.append((QRegularExpression(r'^\s*>.*$'), bq_fmt))

        # link
        link_fmt = QTextCharFormat()
        link_fmt.setForeground(QColor(c["link"]))
        link_fmt.setFontUnderline(True)
        self.rules.append((QRegularExpression(r'\[[^\]]+\]\([^)]+\)'), link_fmt))
        self.rehighlight()

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)
