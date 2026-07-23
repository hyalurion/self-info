"""JSON → rendered UI preview, faithful to the self-info Vue rendering model.

The self-info site consumes its i18n JSON through ``RichText.vue`` (typed
rich-text segments) and ``SectionRenderer.vue`` (discriminated section types).
This module reproduces that rendering as HTML for a ``QTextBrowser`` so the
editor can show *what the site will actually look like* while editing.

Rich-text segment model (recursive ``content``):
    {type:"text",     content: str}
    {type:"ruby",     kanji, reading}          # furigana (shown as 漢字（かな）)
    {type:"highlight",content: [segs] | str, style?}
    {type:"info",     content: [segs] | str}
    {type:"game-card",img, imgAlt, uid}

Section types: birthday / language / acgn / personality / lucky / games /
sns / closing — each rendered the same way the Vue components lay them out.
"""

from __future__ import annotations

import html

from PyQt6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

from app.file_role import ROLE_I18N, ROLE_CHANGELOG
from app.i18n import t
from app.markdown_converter import convert_markdown, have_markdown_lib

_TYPE_BADGE = {
    "object": "{}",
    "array": "[]",
    "string": "ABC",
    "number": "#",
    "bool": "✓",
    "null": "∅",
}


def _esc(s):
    return html.escape(str(s if s is not None else ""))


# ---------------------------------------------------------------------------
# Rich-text (RichText.vue equivalent)
# ---------------------------------------------------------------------------
def _rich_to_html(node, colors, depth: int = 0) -> str:
    """Convert a rich-text node (str | [segs] | seg) into HTML."""
    if isinstance(node, str):
        return _esc(node)
    if isinstance(node, list):
        return "".join(_rich_to_html(x, colors, depth) for x in node)
    if isinstance(node, dict):
        typ = node.get("type")
        if typ == "text":
            return _esc(node.get("content", ""))
        if typ == "ruby":
            kanji = _esc(node.get("kanji", ""))
            reading = _esc(node.get("reading", ""))
            if reading:
                return f'<span class="ruby">{kanji}<span class="rt">（{reading}）</span></span>'
            return kanji
        if typ == "highlight":
            style = node.get("style") or f'color:{colors["hl"]}'
            inner = _rich_to_html(node.get("content", ""), colors, depth + 1)
            return f'<b style="{style}">{inner}</b>'
        if typ == "info":
            inner = _rich_to_html(node.get("content", ""), colors, depth + 1)
            return f'<span class="info">{inner}</span>'
        if typ == "game-card":
            uid = _esc(node.get("uid", ""))
            alt = _esc(node.get("imgAlt", "") or "")
            return f'<span class="card">🎮 {alt} <code>{uid}</code></span>'
        # Unknown type: fall back to its content if present.
        if "content" in node:
            return _rich_to_html(node["content"], colors, depth + 1)
        return _esc(str(node))
    return _esc(node)


# ---------------------------------------------------------------------------
# Section rendering (SectionRenderer.vue equivalent)
# ---------------------------------------------------------------------------
def _render_section(sec: dict, colors: dict) -> str:
    typ = sec.get("type")
    title = _rich_to_html(sec.get("titleRich", "") or sec.get("title", ""), colors)
    out = [f'<div class="section"><h3>{title}</h3>']

    if typ in ("language", "acgn", "birthday"):
        items = sec.get("items", []) or []
        out.append('<ul class="bullets">')
        for it in items:
            out.append(f"<li>{_rich_to_html(it, colors)}</li>")
        out.append("</ul>")

    elif typ == "personality":
        items = sec.get("items", []) or []
        out.append('<ul class="pairs">')
        for it in items:
            if not isinstance(it, dict):
                out.append(f"<li>{_rich_to_html(it, colors)}</li>")
                continue
            label = _rich_to_html(it.get("label", ""), colors)
            value = _rich_to_html(it.get("value", ""), colors)
            note = _rich_to_html(it.get("note", ""), colors)
            out.append(
                f'<li><span class="lbl">{label}</span> '
                f'<span class="val">{value}</span> '
                f'<span class="note">{note}</span></li>'
            )
        out.append("</ul>")

    elif typ == "lucky":
        out.append(f'<p>{_rich_to_html(sec.get("content", ""), colors)}</p>')

    elif typ == "games":
        out.append(f'<p>{_rich_to_html(sec.get("content", ""), colors)}</p>')

    elif typ == "sns":
        link = sec.get("link", {}) or {}
        href = _esc(link.get("href", ""))
        text = _rich_to_html(link.get("text", ""), colors)
        out.append(f'<p class="sns"><a href="{href}">{text}</a></p>')

    elif typ == "closing":
        for line in sec.get("lines", []) or []:
            out.append(f'<p class="closing">{_rich_to_html(line, colors)}</p>')

    else:
        # Unknown / generic section: show its keys as an outline.
        out.append(_outline(sec, colors, depth=0, limit=2))

    out.append("</div>")
    return "".join(out)


# Keys handled by dedicated logic below; everything else is treated as a
# free-form rich-text section (the real sample uses ad-hoc keys like
# hero / about / features whose values are rich-text lists).
_STRUCTURAL_KEYS = {
    "meta", "splashScreen", "header", "sections", "footer", "legal", "hero",
}


def _is_richtext_list(v) -> bool:
    """A list made (mostly) of rich-text segment dicts or plain strings."""
    if not isinstance(v, list) or not v:
        return False
    return all(isinstance(x, (str, dict)) for x in v)


def _humanize(key: str) -> str:
    return key.replace("_", " ").replace("-", " ").strip().title()


def _render_i18n(data: dict, colors: dict) -> str:
    parts = []

    # Page title: prefer meta.title, then a `hero` rich-text block.
    meta = data.get("meta")
    if isinstance(meta, dict) and meta.get("title"):
        parts.append(f'<h1 class="page-title">{_esc(meta["title"])}</h1>')

    hero = data.get("hero")
    if _is_richtext_list(hero) or isinstance(hero, (str, dict)):
        parts.append(f'<h1 class="page-title">{_rich_to_html(hero, colors)}</h1>')

    # Splash banner (privacy consent title) if present.
    splash = data.get("splashScreen")
    if isinstance(splash, dict) and splash.get("title"):
        parts.append(
            f'<div class="banner">🔒 {_rich_to_html(splash.get("titleRich", "") or splash["title"], colors)}</div>'
        )

    # Header lines.
    header = data.get("header")
    if isinstance(header, dict):
        for line in header.get("lines", []) or []:
            parts.append(f'<p class="lead">{_rich_to_html(line, colors)}</p>')

    # Structured sections (SectionRenderer.vue model).
    for sec in data.get("sections", []) or []:
        if isinstance(sec, dict):
            parts.append(_render_section(sec, colors))

    # Free-form rich-text keys (hero already handled above): render each as a
    # titled section so ad-hoc i18n files still preview meaningfully.
    for key, value in data.items():
        if key in _STRUCTURAL_KEYS:
            continue
        if _is_richtext_list(value):
            title = _esc(_humanize(key))
            body = "".join(
                f'<p>{_rich_to_html(seg, colors)}</p>' for seg in value
            )
            parts.append(f'<div class="section"><h3>{title}</h3>{body}</div>')

    # Footer: may be a plain string, a list of lines, or a dict with `lines`.
    footer = data.get("footer")
    flines = []
    if isinstance(footer, str) and footer.strip():
        flines = [footer]
    elif isinstance(footer, list):
        flines = footer
    elif isinstance(footer, dict):
        flines = footer.get("lines", []) or []
    if flines:
        items = "".join(f"<li>{_rich_to_html(ln, colors)}</li>" for ln in flines)
        parts.append(f'<div class="footer"><ul>{items}</ul></div>')

    # Legal / site metadata card.
    legal = data.get("legal")
    if isinstance(legal, dict) and legal:
        rows = []
        for k in ("title", "subtitle", "version", "established", "updated", "author", "email", "policyName"):
            if legal.get(k):
                label = k.capitalize()
                rows.append(f'<div class="kv"><span class="k">{label}</span><span class="v">{_esc(legal[k])}</span></div>')
        if rows:
            parts.append('<div class="legal-card"><h4>Legal / Site</h4>' + "".join(rows) + "</div>")

    return "".join(parts)


def _render_changelog(data, colors: dict) -> str:
    if not isinstance(data, list):
        return _outline(data, colors, 0, 3)
    parts = []
    for e in data:
        if not isinstance(e, dict):
            parts.append(f"<p>{_esc(e)}</p>")
            continue
        v = _esc(e.get("version", ""))
        d = _esc(e.get("date", ""))
        content = e.get("content", "") or ""
        body = convert_markdown(content) if have_markdown_lib() else _esc(content)
        parts.append(
            f'<div class="entry"><h3>v{v} <span class="date">{d}</span></h3>{body}</div>'
        )
    return "".join(parts)


def _outline(node, colors: dict, depth: int, limit: int) -> str:
    if depth > limit:
        return ""
    if isinstance(node, dict):
        items = []
        for k, v in node.items():
            items.append(
                f'<li><span class="k">{_esc(k)}</span> '
                f'<span class="badge">{_TYPE_BADGE.get(_type_of(v), "")}</span>'
                f'{_outline(v, colors, depth + 1, limit)}</li>'
            )
        return f'<ul class="outline">{"".join(items)}</ul>' if items else ""
    if isinstance(node, list) and node:
        sample = node[0]
        inner = _outline(sample, colors, depth + 1, limit)
        return f'<ul class="outline"><li><span class="badge">[ {len(node)} ]</span>{inner}</li></ul>'
    return ""


def _type_of(v) -> str:
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, dict):
        return "object"
    if isinstance(v, list):
        return "array"
    if isinstance(v, str):
        return "string"
    if isinstance(v, (int, float)):
        return "number"
    if v is None:
        return "null"
    return "string"


def _style(colors: dict, lang=None) -> str:
    from app.fonts import css_font_stack

    return f"""
    <style>
      body {{
        background:{colors['bg']}; color:{colors['text']};
        font-family:{css_font_stack(lang)};
        line-height:1.7; margin:0;
      }}
      h1.page-title {{ font-size:1.7em; margin:0 0 0.4em; }}
      h3 {{ font-size:1.15em; margin:0 0 0.5em; color:{colors['accent']}; }}
      h4 {{ margin:0 0 0.4em; color:{colors['muted']}; }}
      .section {{
        background:{colors['section_bg']}; border:1px solid {colors['border']};
        border-radius:12px; padding:10px 14px; margin:10px 0;
      }}
      .banner {{
        background:{colors['section_bg']}; border:1px solid {colors['border']};
        border-radius:12px; padding:8px 12px; margin:8px 0; color:{colors['muted']};
      }}
      .lead {{ font-size:1.05em; margin:0.3em 0; }}
      .closing {{ text-align:center; color:{colors['muted']}; }}
      .ruby .rt {{ color:{colors['muted']}; font-size:0.82em; }}
      .info {{ color:{colors['info']}; }}
      .card {{
        display:inline-block; background:{colors['card']}; border:1px solid {colors['border']};
        border-radius:10px; padding:2px 8px; margin:2px;
      }}
      .card code {{ background:{colors['code_bg']}; border-radius:6px; padding:0 4px; }}
      code {{ background:{colors['code_bg']}; border-radius:6px; padding:1px 5px; font-size:0.92em; }}
      pre {{ background:{colors['code_bg']}; border-radius:12px; padding:1em; white-space:pre-wrap; }}
      a {{ color:{colors['link']}; text-decoration:underline; }}
      .sns a {{
        display:inline-block; padding:8px 16px; background:{colors['card']};
        border:1px solid {colors['border']}; border-radius:20px; text-decoration:none;
      }}
      ul.bullets, ul.pairs {{ margin:0.3em 0 0.3em 1.2em; padding:0; }}
      ul.pairs li {{ margin:0.35em 0; }}
      .lbl {{ font-weight:700; }}
      .note {{ color:{colors['muted']}; font-size:0.9em; }}
      .footer {{ color:{colors['muted']}; margin-top:12px; }}
      .footer ul {{ margin:0; padding-left:1.2em; }}
      .legal-card {{
        border:1px solid {colors['border']}; border-radius:12px; padding:10px 14px; margin:10px 0;
      }}
      .legal-card .kv {{ display:flex; gap:10px; margin:2px 0; }}
      .legal-card .k {{ color:{colors['muted']}; min-width:90px; }}
      .entry {{ border-left:4px solid {colors['accent']}; padding:4px 14px; margin:10px 0; }}
      .entry .date {{ color:{colors['muted']}; font-weight:400; font-size:0.85em; }}
      blockquote {{
        border-left:4px solid {colors['accent']}; background:{colors['section_bg']};
        margin:1em 0; padding:0.6em 1em; border-radius:0 12px 12px 0;
      }}
      table {{ border-collapse:collapse; width:100%; margin:1em 0; }}
      th, td {{ border:1px solid {colors['border']}; padding:0.5em 0.7em; text-align:left; }}
      th {{ background:{colors['section_bg']}; }}
      ul.outline {{ margin:2px 0 2px 1.2em; padding:0; list-style:none; }}
      ul.outline li {{ margin:1px 0; }}
      .badge {{ color:{colors['muted']}; font-size:0.8em; margin-left:4px; }}
    </style>
    """


class JsonPreviewWidget(QWidget):
    """Renders JSON data the way the self-info site would, in a QTextBrowser."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.browser)

    def render(self, data, role: str, lang, colors: dict) -> None:
        if role == ROLE_I18N and isinstance(data, dict):
            body = _render_i18n(data, colors)
        elif role == ROLE_CHANGELOG:
            body = _render_changelog(data, colors)
        else:
            body = _outline(data, colors, 0, 3) or f'<p>{_esc(data)}</p>'
        self.browser.setHtml(_style(colors, lang) + body)

    def show_invalid(self, colors: dict, lang=None) -> None:
        self.browser.setHtml(
            _style(colors, lang) + f'<p style="color:{colors["muted"]}">{_esc(t("json.preview.invalid"))}</p>'
        )
