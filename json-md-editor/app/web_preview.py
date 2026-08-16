"""Embed the real self-info web frontend as the editor's live preview.

This replaces the old ``QTextBrowser`` re-implementation (``json_preview.py`` +
inline HTML) that duplicated the site's Vue rendering logic in Python. Instead,
the preview loads the *actual* built Vue app (``dist/preview.html``) inside a
``QWebEngineView`` and pushes the currently-edited JSON / Markdown through a
tiny JS bridge (``window.__setPreview``). The preview therefore always matches
what the site will really render — no separate renderer to keep in sync.

Serving
-------
The built site references assets with absolute URLs (``/pic/...``,
``/assets/...``, ``/fonts/...``), which require a real HTTP origin (``file://``
can't resolve them). We spin up a tiny ``http.server`` rooted at the project
``dist/`` directory, bound to ``127.0.0.1`` only (no firewall prompt) on an
ephemeral port. One server is shared by all preview widgets for the process
lifetime.
"""

from __future__ import annotations

import json
import os
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QMenu

# ---------------------------------------------------------------------------
# Dist discovery
# ---------------------------------------------------------------------------
def _find_dist_dir() -> str | None:
    """Locate the built ``dist/`` directory containing ``preview.html``."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.environ.get("SELFINFO_DIST_DIR"),
        os.path.abspath(os.path.join(here, "..", "..", "dist")),   # project root
        os.path.abspath(os.path.join(here, "..", "dist")),
    ]
    for c in candidates:
        if c and os.path.isfile(os.path.join(c, "preview.html")):
            return c
    return None


class _PreviewHandler(SimpleHTTPRequestHandler):
    """Serve the built site with correct MIME types and cache headers.

    Python's stdlib ``mimetypes`` doesn't know ``.woff2`` (it falls back to
    ``application/octet-stream``), which makes Chromium refuse to load the
    site's webfonts — the preview then silently falls back to system fonts and
    no longer looks like production. We also add ``Cache-Control`` so the
    multi-MB fonts are fetched once instead of on every preview page load.
    """

    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".woff2": "font/woff2",
        ".woff": "font/woff",
        ".ttf": "font/ttf",
        ".otf": "font/otf",
        ".avif": "image/avif",
        ".opus": "audio/opus",
        ".svg": "image/svg+xml",
        ".js": "text/javascript",
        ".mjs": "text/javascript",
        ".css": "text/css",
    }

    def log_message(self, _format, *_args):
        return

    def end_headers(self):
        path = self.path.split("?", 1)[0]
        if path.startswith("/assets/"):
            # Vite-hashed bundles — immutable, cache effectively forever.
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        elif path.endswith((".woff2", ".woff", ".ttf", ".otf", ".avif", ".opus", ".jpg", ".jpeg", ".png", ".svg", ".gif")):
            # Large static media — cache for a day.
            self.send_header("Cache-Control", "public, max-age=86400")
        else:
            # HTML — revalidate so the editor always sees a fresh build.
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()


# ---------------------------------------------------------------------------
# Shared localhost server (singleton)
# ---------------------------------------------------------------------------
_SERVER: ThreadingHTTPServer | None = None
_SERVER_LOCK = threading.Lock()


def _ensure_server() -> ThreadingHTTPServer | None:
    """Return the shared HTTP server, creating it on first use."""
    global _SERVER
    with _SERVER_LOCK:
        if _SERVER is not None:
            return _SERVER
        dist = _find_dist_dir()
        if dist is None:
            return None
        handler = partial(_PreviewHandler, directory=dist)
        try:
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        except OSError:
            return None
        server.daemon_threads = True
        threading.Thread(target=server.serve_forever, daemon=True).start()
        _SERVER = server
        return server


def _fallback_html() -> str:
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='background:#171127;color:#ece6ff;font-family:sans-serif;"
        "padding:40px;text-align:center'>"
        "<h2>Preview unavailable</h2>"
        "<p>The built frontend (<code>dist/preview.html</code>) was not found.</p>"
        "<p>Run <code>npm run build</code> in the project root, or set "
        "<code>SELFINFO_DIST_DIR</code> to the dist directory.</p>"
        "<script>window.__setPreview = function(){};</script>"
        "</body></html>"
    )


# ---------------------------------------------------------------------------
# Pre-warm (optional): start Chromium + fetch the default font in the
# background so the first real preview isn't paying the cold-start cost.
# ---------------------------------------------------------------------------
_PREWARM_VIEW: QWebEngineView | None = None


def prewarm() -> None:
    """Warm up QtWebEngine (Chromium process + webfont cache) in the background.

    Creates a hidden view that loads the preview page once and keeps it alive.
    Subsequent ``WebPreview`` instances share the same default profile, so the
    renderer process and the HTTP cache (fonts, JS/CSS) are already hot.
    Safe to call once at startup, after ``QApplication`` exists.
    """
    global _PREWARM_VIEW
    if _PREWARM_VIEW is not None:
        return
    server = _ensure_server()
    if server is None:
        return
    try:
        view = QWebEngineView()
        view.setVisible(False)
        view.setMinimumSize(400, 300)
        _PREWARM_VIEW = view
        port = server.server_address[1]
        view.load(QUrl(f"http://127.0.0.1:{port}/preview.html"))
    except Exception:  # noqa: BLE001
        _PREWARM_VIEW = None


# ---------------------------------------------------------------------------
# Preview widget
# ---------------------------------------------------------------------------
class WebPreview(QWebEngineView):
    """Render a payload dict ({mode, lang, data}) through the real site UI."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._loaded = False
        self._pending: dict | None = None

        server = _ensure_server()
        if server is None:
            self.setHtml(_fallback_html(), QUrl("about:blank"))
        else:
            port = server.server_address[1]
            self.load(QUrl(f"http://127.0.0.1:{port}/preview.html"))
        self.loadFinished.connect(self._on_load_finished)

    # -- public API ----------------------------------------------------------
    def render(self, payload: dict) -> None:
        """Push a preview payload; queues until the page has finished loading."""
        if not self._loaded:
            self._pending = payload
            return
        self._inject(payload)

    # -- internals ----------------------------------------------------------
    def _on_load_finished(self, ok: bool) -> None:
        self._loaded = True
        if ok and self._pending is not None:
            pending, self._pending = self._pending, None
            self._inject(pending)

    def _inject(self, payload: dict) -> None:
        # Serialize with raw Unicode (halves the payload size for CJK content
        # vs ASCII \uXXXX escaping) and only escape the two characters that are
        # illegal in JS string literals. Still valid as a JS object literal.
        raw = json.dumps(payload, ensure_ascii=False)
        raw = raw.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
        js = "window.__setPreview && window.__setPreview(" + raw + ");"
        self.page().runJavaScript(js)

    # -- context menu --------------------------------------------------------
    def contextMenuEvent(self, event) -> None:
        """Show a context menu with Copy / Select All / Reload.

        Qt6 removed ``QWebEnginePage.createStandardContextMenu()``, so build a
        small menu from the page's bound actions — those carry the correct
        enabled state (e.g. Copy is only enabled while text is selected).
        """
        page = self.page()
        menu = QMenu(self)
        menu.addAction(page.action(QWebEnginePage.WebAction.Copy))
        menu.addAction(page.action(QWebEnginePage.WebAction.SelectAll))
        menu.addSeparator()
        menu.addAction(page.action(QWebEnginePage.WebAction.Reload))
        menu.exec(event.globalPos())
