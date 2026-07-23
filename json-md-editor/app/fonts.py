"""Custom font loading for the editor UI.

Purpose
-------
The self-info site uses bespoke fonts per locale:

  * ``zh-Hans`` -> ``LXGW WenKai GB``  (fonts/LXGWWenKaiGB-Regular.ttf)
  * ``zh-TW``   -> ``LXGW WenKai TC``  (fonts/LXGWWenKaiTC-Regular.ttf)
  * ``ja`` / ``en`` -> ``Klee One``    (fonts/KleeOne-Regular.ttf)

To keep the PyQt6 editor visually consistent with the rendered site, we ship
the converted TTF files next to the app and register them through
``QFontDatabase`` at startup.  Qt's font engine (FreeType) cannot read woff2,
so the woff2 sources (in ``public/fonts``) were pre-converted to TTF once
during packaging — at runtime we just ``addApplicationFont`` the local TTFs,
which is effectively instant (no decompression).

The TTFs are large (LXGW WenKai has ~40k glyphs); that is an accepted trade-off
for zero startup delay.
"""

from __future__ import annotations

import os
import sys

from PyQt6.QtGui import QFontDatabase

# Bundled TTF directory (inside the app package).
_FONTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fonts"))

# lang code -> (preferred family name, bundled TTF filename)
_FONT_FILES = {
    "zh-Hans": (
        "LXGW WenKai GB",
        "LXGWWenKaiGB-Regular.ttf",
    ),
    "zh-TW": (
        "LXGW WenKai TC",
        "LXGWWenKaiTC-Regular.ttf",
    ),
    "klee": (
        "Klee One",
        "KleeOne-Regular.ttf",
    ),
}

# Resolved family name per key (filled once fonts are registered).
_REGISTERED: dict[str, str] = {}
_LOADED = False


def load_application_fonts() -> None:
    """Synchronously register all bundled TTF fonts.

    Fast (no decompression) — safe to call on the GUI thread at startup.
    Idempotent.  Falls back to the preferred name on any failure so callers
    can still build a font-family list.
    """
    global _LOADED
    if _LOADED:
        return
    for key, (preferred, fname) in _FONT_FILES.items():
        path = os.path.join(_FONTS_DIR, fname)
        if not os.path.exists(path):
            print(f"[fonts] missing {fname!r} — using fallback", file=sys.stderr)
            _REGISTERED[key] = preferred
            continue
        try:
            fid = QFontDatabase.addApplicationFont(path)
            families = QFontDatabase.applicationFontFamilies(fid)
            _REGISTERED[key] = families[0] if families else preferred
        except Exception as exc:  # noqa: BLE001
            print(f"[fonts] could not load {preferred!r}: {exc}", file=sys.stderr)
            _REGISTERED[key] = preferred
    _LOADED = True


def registered_family_for_lang(lang: str) -> str:
    """Return the custom font family name for a UI language.

    Falls back to a sensible system font if the custom font failed to load.
    Does NOT trigger font loading — call :func:`load_application_fonts` first.
    """
    if lang == "zh-Hans":
        return _REGISTERED.get("zh-Hans", "Microsoft YaHei")
    if lang == "zh-TW":
        return _REGISTERED.get("zh-TW", "Microsoft YaHei")
    # ja / en and anything else use Klee One.
    return _REGISTERED.get("klee", "Segoe UI")


def build_font_families(lang: str) -> list[str]:
    """Return a full font-family fallback list for the given language.

    The custom webfont comes first, followed by platform UI fonts so that any
    glyph the webfont lacks (e.g. emoji, symbols) still renders via the system.
    """
    primary = registered_family_for_lang(lang)
    fallbacks = [
        "Segoe UI",
        "Microsoft YaHei UI",
        "Microsoft YaHei",
        "PingFang SC",
        "Hiragino Sans",
        "Noto Sans CJK SC",
        "sans-serif",
    ]
    if primary in fallbacks:
        fallbacks.remove(primary)
    return [primary, *fallbacks]


def css_font_stack(lang: str | None = None) -> str:
    """Return a CSS ``font-family`` value for use inside preview HTML.

    Font names containing spaces are quoted.  Falls back to the current UI
    language when ``lang`` is not supplied.
    """
    if lang is None:
        from app.i18n import get_lang  # noqa: PLC0415

        lang = get_lang()
    families = build_font_families(lang)
    quoted = ", ".join(
        f'"{f}"' if " " in f or f in ("sans-serif", "serif", "monospace") else f
        for f in families
    )
    return quoted
