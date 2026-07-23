"""Markdown to HTML. Prefer the `markdown` library, fallback to built-in lightweight converter."""

import re

try:
    import markdown as _md

    _HAVE_MD = True
except Exception:  # noqa: BLE001
    _HAVE_MD = False


def have_markdown_lib():
    return _HAVE_MD


def convert_markdown(text):
    """Convert Markdown text to HTML."""
    if _HAVE_MD:
        return _md.markdown(
            text,
            extensions=["tables", "fenced_code", "toc", "nl2br", "sane_lists"],
        )
    return _fallback(text)


def _escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline(s):
    s = _escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*([^*]+?)\*", r"<em>\1</em>", s)
    s = re.sub(r"__([^_]+?)__", r"<strong>\1</strong>", s)
    s = re.sub(r"_([^_]+?)_", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def _fallback(text):
    lines = text.split("\n")
    html = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        # Fenced Code Blocks
        if line.strip().startswith("```"):
            lang = line.strip()[3:].strip()
            code = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code.append(_escape(lines[i]))
                i += 1
            i += 1
            cls = f' class="language-{lang}"' if lang else ""
            html.append(f"<pre><code{cls}>\n" + "\n".join(code) + "</code></pre>")
            continue
        # Headers
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            html.append(f"<h{level}>{_inline(m.group(2).strip())}</h{level}>")
            i += 1
            continue
        # Horizontal Lines
        if re.match(r"^\s*([-*_])(\s*\1){2,}\s*$", line):
            html.append("<hr/>")
            i += 1
            continue
        # Quotes
        if re.match(r"^\s*>\s?", line):
            quote = []
            while i < n and re.match(r"^\s*>\s?", lines[i]):
                quote.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            html.append("<blockquote>" + _inline(" ".join(quote)) + "</blockquote>")
            continue
        # Unordered/Ordered Lists
        if re.match(r"^\s*([-*+]|\d+\.)\s+", line):
            ordered = bool(re.match(r"^\s*\d+\.\s+", line))
            tag = "ol" if ordered else "ul"
            items = []
            while i < n and re.match(r"^\s*([-*+]|\d+\.)\s+", lines[i]):
                content = re.sub(r"^\s*([-*+]|\d+\.)\s+", "", lines[i])
                items.append("<li>" + _inline(content) + "</li>")
                i += 1
            html.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
            continue
        # Empty Lines
        if not line.strip():
            i += 1
            continue
        # Paragraphs
        para = [line]
        i += 1
        while i < n and lines[i].strip() and not re.match(r"^(#{1,6}\s|\s*>\s?|\s*([-*+]|\d+\.)\s+|```)", lines[i]):
            para.append(lines[i])
            i += 1
        html.append("<p>" + _inline(" ".join(para)) + "</p>")
    return "\n".join(html)
