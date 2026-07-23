"""Application entry point."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from app.fonts import build_font_families, load_application_fonts
from app.i18n import get_lang
from app.main_window import MainWindow


def _apply_app_font(app):
    """Apply the per-locale font to the whole application."""
    font = QFont()
    font.setFamilies(build_font_families(get_lang()))
    font.setPointSize(10)
    app.setFont(font)


def main():
    app = QApplication(sys.argv)
    # App identity.
    app.setApplicationName("JSON & Markdown Editor")
    app.setOrganizationName("Hyalurion")
    # Load the site's bundled custom fonts (pre-converted TTFs, instant — no
    # decompression) so the editor matches the self-info site typography.
    load_application_fonts()
    # Apply the per-locale font to the whole UI.
    _apply_app_font(app)
    # CRITICAL: Force Fusion style so our QSS can fully override widget rendering.
    # On Windows, the native style ignores most QSS rules for QMenuBar/QToolBar.
    from PyQt6.QtWidgets import QStyleFactory  # noqa: PLC0415
    app.setStyle(QStyleFactory.create("Fusion"))
    # Prevent native menu bar on macOS/Linux; harmless on Windows.
    # (High-DPI scaling is enabled by default in PyQt6 — the old
    #  AA_EnableHighDpiScaling / AA_UseHighDpiPixmaps attributes were removed.)
    app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, True)
    # The actual theme (System / Light / Dark, persisted) is applied by
    # MainWindow after it restores the saved preference. We only set the base
    # style here so the window paints correctly before that.
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
