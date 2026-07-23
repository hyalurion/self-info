"""Modern "liquid-glass / purple" theme for the editor (QSS).

Two palettes are provided — a deep-violet *dark* theme and a soft-lavender
*light* theme — both generated from a single template so they never drift
apart. ``apply_theme(app, lang, mode)`` selects among three modes:

  * ``"dark"``   — always dark
  * ``"light"``  — always light
  * ``"system"`` — follow the OS colour scheme (via
    ``QGuiApplication.styleHints().colorScheme()``), and live-update when the
    user flips their OS theme.

The active palette colours are also exposed via ``get_preview_colors(mode)``
so that rendered previews (JSON / Markdown) can embed matching inline colours.

IMPORTANT: All colours use **solid hex** notation. Qt's QSS parser does NOT
reliably handle ``rgba()`` in border-color / background-color properties —
it silently drops the rule, leaving widgets unstyled.
"""

from __future__ import annotations

from string import Template

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QGuiApplication, QPalette

# ---------------------------------------------------------------------------
# Palette definitions. The template below references these names.
#
# All values are solid hex (#rrggbb).  No rgba() — see module docstring.
# ---------------------------------------------------------------------------
DARK = {
    "BG_0": "#100b1c",
    "BG_1": "#171127",
    "BG_2": "#1f1733",
    "BG_3": "#271d40",
    "BG_4": "#2e234a",          # hover/active surface
    "TEXT": "#ece6ff",
    "TEXT_MUTED": "#a99fce",
    "BORDER": "#2e244a",         # subtle border on dark
    "BORDER_STRONG": "#4a3877",  # stronger border / focus ring
    "ACCENT": "#b388ff",
    "ACCENT_SOFT": "#c9a6ff",
    "ACCENT_DIM": "#7c5cc4",
    "TEXT_ON_ACCENT": "#1a1030",
    "SELECT_BG": "#7c5cc4",
    "SELECT_FG": "#ffffff",
}

LIGHT = {
    "BG_0": "#f4f1fb",
    "BG_1": "#ffffff",
    "BG_2": "#f0ecfa",
    "BG_3": "#e6dffa",
    "BG_4": "#ddd3f5",           # hover/active surface
    "TEXT": "#2a2440",
    "TEXT_MUTED": "#6b6390",
    "BORDER": "#d0c6e4",         # subtle border on light
    "BORDER_STRONG": "#b29ee0",  # stronger border / focus ring
    "ACCENT": "#7c5cc4",
    "ACCENT_SOFT": "#9a7fe0",
    "ACCENT_DIM": "#6a4fb0",
    "TEXT_ON_ACCENT": "#ffffff",
    "SELECT_BG": "#7c5cc4",
    "SELECT_FG": "#ffffff",
}

# Preview colours (for embedded HTML in QTextBrowser previews).
PREVIEW_COLORS = {
    "dark": {
        "bg": "#171127",
        "text": "#ece6ff",
        "accent": "#c9a6ff",
        "muted": "#a99fce",
        "border": "rgba(179,136,255,0.30)",
        "code_bg": "rgba(128,128,128,0.15)",
        "hl": "#d5ffbf",
        "info": "#b9aee0",
        "link": "#c9a6ff",
        "card": "rgba(179,136,255,0.14)",
        "section_bg": "rgba(179,136,255,0.06)",
    },
    "light": {
        "bg": "#ffffff",
        "text": "#2a2440",
        "accent": "#7c5cc4",
        "muted": "#6b6390",
        "border": "rgba(124,92,196,0.35)",
        "code_bg": "#f0ecfa",
        "hl": "#512da8",
        "info": "#6b6390",
        "link": "#7c5cc4",
        "card": "rgba(124,92,196,0.10)",
        "section_bg": "rgba(124,92,196,0.05)",
    },
}

# Code-editor colours (line-number gutter, current line, syntax tokens). These
# are painted / applied programmatically (not via QSS) so they must follow the
# active theme too, otherwise light theme keeps the dark VS-Code palette and
# the text becomes unreadable.
EDITOR_COLORS = {
    "dark": {
        "editor_bg": "#171127",
        "editor_fg": "#ece6ff",
        "gutter_bg": "#120e20",
        "gutter_fg": "#6f6a8f",
        "gutter_fg_current": "#c9a6ff",
        "current_line": "#201933",
        "str": "#c9e8a0",
        "num": "#f2b880",
        "kw": "#82aaff",
        "key": "#c9a6ff",
        "heading": "#c9a6ff",
        "bold": "#f2b880",
        "italic": "#c9a6ff",
        "code": "#c9e8a0",
        "list": "#7fd6c2",
        "quote": "#9a90c0",
        "link": "#82aaff",
    },
    "light": {
        "editor_bg": "#ffffff",
        "editor_fg": "#2a2440",
        "gutter_bg": "#ebe5f8",
        "gutter_fg": "#a49cc4",
        "gutter_fg_current": "#7c5cc4",
        "current_line": "#f2edfb",
        "str": "#0a7d3c",
        "num": "#b8562f",
        "kw": "#1f5fd0",
        "key": "#6a2fb0",
        "heading": "#6a2fb0",
        "bold": "#b8562f",
        "italic": "#6a2fb0",
        "code": "#0a7d3c",
        "list": "#0f8a78",
        "quote": "#6b6390",
        "link": "#1f5fd0",
    },
}

# ---------------------------------------------------------------------------
# Single QSS template. Literal CSS braces stay as-is; only $-prefixed names
# are substituted, so we avoid doubling every brace.
#
# Design goals:
#   - Premium feel: consistent spacing, rounded corners, subtle depth.
#   - Every widget type covered (no native fallbacks on Windows/macOS).
#   - Dock descendants explicitly styled (Windows caches native colours).
#   - Scrollbars thin and modern.
# ---------------------------------------------------------------------------
_QSS_TEMPLATE = """
/* ================================================================
   BASE – reset all widgets to the theme palette
   ================================================================ */
QWidget {
    background-color: $BG_0;
    color: $TEXT;
    font-family: $APP_FONT;
    font-size: 13px;
}
QMainWindow, QWidget#central {
    background-color: $BG_0;
}

/* ================================================================
   MENU BAR – must override native rendering on every platform
   ================================================================ */
QMenuBar {
    background-color: $BG_1;
    padding: 4px 10px;
    border-bottom: 1px solid $BORDER;
    font-weight: 500;
    spacing: 6px;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
    border-radius: 6px;
    margin: 0 1px;
}
QMenuBar::item:selected {
    background-color: $BG_3;
    color: $ACCENT_SOFT;
}
QMenuBar::item:pressed {
    background-color: $ACCENT_DIM;
    color: #ffffff;
}
QMenu {
    background-color: $BG_2;
    border: 1px solid $BORDER_STRONG;
    border-radius: 10px;
    padding: 6px 4px;
}
QMenu::item {
    padding: 7px 26px 7px 14px;
    border-radius: 6px;
    margin: 1px 4px;
}
QMenu::item:selected {
    background-color: $ACCENT_DIM;
    color: #ffffff;
}
QMenu::separator {
    height: 1px;
    background-color: $BORDER;
    margin: 5px 10px;
}

/* ================================================================
   TOOL BAR
   ================================================================ */
QToolBar {
    background-color: $BG_1;
    border: none;
    border-bottom: 1px solid $BORDER;
    spacing: 4px;
    padding: 6px 12px;
    font-weight: 500;
}
QToolBar::separator {
    width: 1px;
    background-color: $BORDER;
    margin: 4px 8px;
}
QToolBar::handle {
    width: 3px;
    background-color: $BORDER;
    border-radius: 2px;
    margin: 4px 2px;
}
QToolBar QLabel {
    color: $TEXT_MUTED;
    padding: 0 4px 0 6px;
    font-weight: 500;
}
QToolButton {
    background-color: transparent;
    color: $TEXT;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 6px 11px;
    min-height: 16px;
    font-weight: 500;
}
QToolButton:hover {
    background-color: $BG_3;
    border: 1px solid $BORDER;
}
QToolButton:pressed {
    background-color: $ACCENT_DIM;
    color: #ffffff;
    border: 1px solid $ACCENT_DIM;
}
QToolButton:checked {
    background-color: $ACCENT_DIM;
    color: #ffffff;
    border: 1px solid $ACCENT_SOFT;
}
QToolButton:disabled {
    color: $TEXT_MUTED;
}
QToolButton::menu-indicator {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    right: 6px;
}

/* ================================================================
   BUTTONS
   ================================================================ */
QPushButton {
    background-color: $BG_2;
    color: $TEXT;
    border: 1px solid $BORDER;
    border-radius: 8px;
    padding: 6px 14px;
    min-height: 18px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: $BG_3;
    border: 1px solid $BORDER_STRONG;
}
QPushButton:pressed {
    background-color: $ACCENT_DIM;
    color: #ffffff;
    border: 1px solid $ACCENT_DIM;
}
QPushButton:checked {
    background-color: $ACCENT_DIM;
    color: #ffffff;
    border: 1px solid $ACCENT_SOFT;
}
QPushButton:disabled {
    color: $TEXT_MUTED;
    background-color: $BG_1;
    border-color: $BORDER;
}
QPushButton#primary {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 $ACCENT, stop:1 $ACCENT_SOFT);
    color: $TEXT_ON_ACCENT;
    font-weight: 600;
    border: none;
}

/* ================================================================
   COMBO BOX (language / theme selector)
   ================================================================ */
QComboBox {
    background-color: $BG_2;
    color: $TEXT;
    border: 1px solid $BORDER;
    border-radius: 8px;
    padding: 5px 10px;
    min-height: 18px;
    min-width: 80px;
}
QComboBox:hover {
    border: 1px solid $BORDER_STRONG;
    background-color: $BG_3;
}
QComboBox:on {
    border: 1px solid $ACCENT_SOFT;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 20px;
    border: none;
    border-left: 1px solid $BORDER;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}
QComboBox::down-arrow {
    image: none;
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid $TEXT_MUTED;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: $BG_2;
    color: $TEXT;
    border: 1px solid $BORDER_STRONG;
    border-radius: 8px;
    padding: 4px;
    outline: none;
    selection-background-color: $ACCENT_DIM;
    selection-color: #ffffff;
}

/* ================================================================
   TEXT INPUTS
   ================================================================ */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox {
    background-color: $BG_2;
    color: $TEXT;
    border: 1px solid $BORDER;
    border-radius: 8px;
    padding: 6px 10px;
    selection-background-color: $ACCENT_DIM;
    selection-color: #ffffff;
}
QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {
    border: 1px solid $BORDER_STRONG;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus {
    border: 1px solid $ACCENT_SOFT;
    background-color: $BG_1;
}

/* ================================================================
   TAB WIDGET
   ================================================================ */
QTabWidget::pane {
    border: 1px solid $BORDER;
    border-radius: 10px;
    top: -1px;
    background-color: $BG_0;
    padding: 2px;
}
QTabBar {
    qproperty-drawBase: 0;
    background: transparent;
}
QTabBar::tab {
    background-color: transparent;
    color: $TEXT_MUTED;
    border: 1px solid transparent;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 7px 16px;
    margin-right: 2px;
    font-weight: 500;
}
QTabBar::tab:selected {
    background-color: $BG_2;
    color: $TEXT;
    border: 1px solid $BORDER;
    border-bottom: 2px solid $ACCENT;
}
QTabBar::tab:hover:!selected {
    background-color: $BG_1;
    color: $TEXT;
}
QTabBar::close-button {
    image: none;
    subcontrol-position: right;
}

/* ================================================================
   TREE / LIST VIEWS (file explorer, JSON tree)
   ================================================================ */
QTreeView, QListWidget {
    background-color: $BG_1;
    color: $TEXT;
    border: 1px solid $BORDER;
    border-radius: 10px;
    padding: 4px;
    outline: none;
    alternate-background-color: $BG_2;
}
QTreeView::item, QListWidget::item {
    padding: 5px 6px;
    border-radius: 6px;
    min-height: 18px;
}
QTreeView::item:hover, QListWidget::item:hover {
    background-color: $BG_3;
}
QTreeView::item:selected, QListWidget::item:selected {
    background-color: $ACCENT_DIM;
    color: #ffffff;
}
QHeaderView::section {
    background-color: $BG_2;
    color: $TEXT_MUTED;
    border: none;
    border-bottom: 1px solid $BORDER;
    padding: 6px 8px;
    font-weight: 600;
    font-size: 12px;
}
QHeaderView::section:first {
    border-top-left-radius: 6px;
}
QHeaderView::section:last {
    border-top-right-radius: 6px;
}
QTreeView::indicator, QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border: 1px solid $BORDER_STRONG;
    border-radius: 4px;
    background: $BG_2;
}
QTreeView::indicator:checked, QCheckBox::indicator:checked {
    background: $ACCENT;
    border: 1px solid $ACCENT_SOFT;
}

/* ================================================================
   CHECK BOX
   ================================================================ */
QCheckBox {
    background: transparent;
    spacing: 6px;
    color: $TEXT_MUTED;
}
QCheckBox::indicator:hover {
    border: 1px solid $ACCENT_SOFT;
}

/* ================================================================
   STATUS BAR
   ================================================================ */
QStatusBar {
    background-color: $BG_1;
    color: $TEXT_MUTED;
    border: none;
    border-top: 1px solid $BORDER;
    padding: 4px 10px;
    font-size: 12px;
}
QStatusBar::item {
    border: none;
}
QStatusBar QLabel {
    color: $TEXT_MUTED;
    padding: 0 4px;
}
QLabel#roleChip {
    background-color: $BG_3;
    color: $ACCENT_SOFT;
    border: 1px solid $BORDER;
    border-radius: 8px;
    padding: 2px 10px;
    font-size: 12px;
}

/* ================================================================
   DOCK WIDGET – critical: style ALL descendants so the explorer
   (line-edit, button, tree) always follows the active theme.
   Windows caches native colours inside docks without this.
   ================================================================ */
QDockWidget {
    titlebar-normal-icon: none;
    titlebar-close-icon: none;
    titlebar-float-icon: none;
    border: 1px solid $BORDER;
    border-radius: 10px;
    color: $TEXT_MUTED;
    font-weight: 600;
}
QDockWidget::title {
    background-color: $BG_1;
    padding: 8px 10px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    border-bottom: 1px solid $BORDER;
    text-align: left;
    font-size: 12px;
}
QDockWidget > QWidget,
QDockWidget QWidget {
    background-color: $BG_0;
    color: $TEXT;
}
QDockWidget QLineEdit,
QDockWidget QPushButton,
QDockWidget QLabel,
QDockWidget QTreeView {
    background-color: $BG_1;
    color: $TEXT;
    border-color: $BORDER;
}
QDockWidget QLineEdit:focus {
    background-color: $BG_2;
    border-color: $ACCENT_SOFT;
}

/* ================================================================
   SPLITTER
   ================================================================ */
QSplitter::handle {
    background-color: transparent;
}
QSplitter::handle:hover {
    background-color: $BORDER_STRONG;
    border-radius: 2px;
}
QSplitter::handle:horizontal {
    width: 5px;
}
QSplitter::handle:vertical {
    height: 5px;
}

/* ================================================================
   SCROLL BARS – thin & modern
   ================================================================ */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background-color: $BG_3;
    border-radius: 5px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover {
    background-color: $ACCENT_DIM;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background-color: $BG_3;
    border-radius: 5px;
    min-width: 28px;
}
QScrollBar::handle:horizontal:hover {
    background-color: $ACCENT_DIM;
}
QScrollBar::add-line, QScrollBar::sub-line {
    width: 0;
    height: 0;
}
QScrollBar::add-page, QScrollBar::sub-page {
    background: transparent;
}

/* ================================================================
   DIALOGS & GROUP BOXES
   ================================================================ */
QDialog {
    background-color: $BG_0;
    border: 1px solid $BORDER;
    border-radius: 14px;
}
QGroupBox {
    border: 1px solid $BORDER;
    border-radius: 10px;
    margin-top: 12px;
    padding: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 5px;
    color: $ACCENT_SOFT;
    font-weight: 600;
}
QFormLayout QLabel {
    color: $TEXT_MUTED;
}

/* ================================================================
   TEXT BROWSER (markdown / JSON preview)
   ================================================================ */
QTextBrowser {
    background-color: $BG_1;
    color: $TEXT;
    border: 1px solid $BORDER;
    border-radius: 10px;
    padding: 14px;
    selection-background-color: $ACCENT_DIM;
    selection-color: #ffffff;
}

/* ================================================================
   CODE EDITOR (plain-text edit used for source code)
   ================================================================ */
QPlainTextEdit#codeEditor {
    border-radius: 10px;
    background-color: $BG_1;
}

/* ================================================================
   TOOLTIP
   ================================================================ */
QToolTip {
    background-color: $BG_3;
    color: $TEXT;
    border: 1px solid $BORDER_STRONG;
    border-radius: 8px;
    padding: 5px 9px;
}

/* ================================================================
   MISCELLANEOUS
   ================================================================ */
QFrame[frameShape="4"], QFrame#separator {
    background-color: $BORDER;
}
"""

# The mode most recently applied (so previews can resolve "system" live).
CURRENT_MODE = "system"


# ---------------------------------------------------------------------------
# Mode resolution + application
# ---------------------------------------------------------------------------
def resolve_scheme(mode: str) -> str:
    """Return the concrete scheme ("light" / "dark") for a mode.

    ``"system"`` reads the OS colour scheme through Qt's style hints.
    """
    if mode in ("light", "dark"):
        return mode
    app = QGuiApplication.instance()
    if app is not None:
        try:
            cs = app.styleHints().colorScheme()
            if cs == Qt.ColorScheme.Dark:
                return "dark"
            if cs == Qt.ColorScheme.Light:
                return "light"
        except Exception:  # noqa: BLE001
            pass
    return "dark"


def get_preview_colors(mode: str | None = None) -> dict:
    """Return the active preview colour dict for embedding into HTML.

    With no explicit mode, uses the currently applied theme mode (so a
    "system" theme follows the live OS scheme).
    """
    if mode is None:
        mode = CURRENT_MODE
    return PREVIEW_COLORS[resolve_scheme(mode)]


def get_editor_colors(mode: str | None = None) -> dict:
    """Return the active code-editor colour dict (gutter / current line /
    syntax tokens) for the current or given theme mode."""
    if mode is None:
        mode = CURRENT_MODE
    return EDITOR_COLORS[resolve_scheme(mode)]


def _apply_palette(app, scheme: str) -> None:
    p = DARK if scheme == "dark" else LIGHT
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(p["BG_0"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(p["TEXT"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(p["BG_2"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(p["BG_1"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(p["TEXT"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(p["BG_2"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(p["TEXT"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(p["SELECT_BG"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(p["SELECT_FG"]))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(p["BG_2"]))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(p["TEXT"]))
    palette.setColor(QPalette.ColorRole.Link, QColor(p["ACCENT_SOFT"]))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(p["TEXT_MUTED"]))
    app.setPalette(palette)


def apply_theme(app, lang: str | None = None, mode: str = "system") -> str:
    """Apply the theme for ``mode`` (light/dark/system) to ``app``.

    The active UI language selects the matching custom webfont (LXGW WenKai GB
    for zh-Hans, LXGW WenKai TC for zh-TW, Klee One for ja/en) which is injected
    into the QSS so every widget renders with the site's typography.  Returns the
    concrete scheme that was applied.
    """
    if lang is None:
        from app.i18n import get_lang  # noqa: PLC0415

        lang = get_lang()
    from app.fonts import css_font_stack  # noqa: PLC0415

    scheme = resolve_scheme(mode)
    base = DARK if scheme == "dark" else LIGHT
    qss = Template(_QSS_TEMPLATE).substitute({**base, "APP_FONT": css_font_stack(lang)})
    app.setStyleSheet(qss)
    _apply_palette(app, scheme)
    global CURRENT_MODE
    CURRENT_MODE = mode
    return scheme
