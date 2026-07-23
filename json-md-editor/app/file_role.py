"""Detect the *role* of a JSON / Markdown file within the self-info project.

The editor is project-aware: it recognises three semantic roles that the
self-info Vue app actually consumes, plus two generic fallbacks.

Roles
-----
- i18n      ``…/src/data/i18n/<lang>.json``   site content (rich-text arrays)
- changelog ``…/src/data/changelogs/<lang>.json``  array of {version,date,content}
- legal     ``…/src/data/legal/*.<md|markdown>``  per-language privacy policy
- generic_json / generic_md                     any other file by extension
"""
from __future__ import annotations

import os
import re

from app.i18n import normalize_lang

# Canonical role constants.
ROLE_I18N = "i18n"
ROLE_CHANGELOG = "changelog"
ROLE_LEGAL = "legal"
ROLE_GENERIC_JSON = "generic_json"
ROLE_GENERIC_MD = "generic_md"


def detect_role(path: str | None):
    """Return ``(role, lang_or_None)`` for the given file path.

    ``lang`` is a canonical code (ja/en/zh-Hans/zh-TW) when the file belongs to
    a language-specific dataset, otherwise ``None``.
    """
    if not path:
        return ROLE_GENERIC_JSON, None

    norm = os.path.normcase(os.path.abspath(path))
    parts = norm.split(os.sep)
    lower = norm.lower()

    # Walk up looking for the project markers.
    # i18n: .../src/data/i18n/<lang>.json
    # changelogs: .../src/data/changelogs/<lang>.json
    # legal: .../src/data/legal/<name>.md
    for i, part in enumerate(parts):
        pl = part.lower()
        if pl == "i18n" and i + 1 < len(parts):
            fname = parts[i + 1]
            lang = _lang_from_filename(fname)
            return ROLE_I18N, lang
        if pl == "changelogs" and i + 1 < len(parts):
            fname = parts[i + 1]
            lang = _lang_from_filename(fname)
            return ROLE_CHANGELOG, lang
        if pl == "legal" and i + 1 < len(parts):
            fname = parts[i + 1]
            lang = _lang_from_filename(fname)
            return ROLE_LEGAL, lang

    # Fallback by extension.
    if lower.endswith(".json"):
        return ROLE_GENERIC_JSON, None
    if lower.endswith((".md", ".markdown")):
        return ROLE_GENERIC_MD, None
    return ROLE_GENERIC_JSON, None


def _lang_from_filename(fname: str):
    """Extract a canonical language code from a dataset filename.

    Handles both i18n codes (ja/en/zh-Hans/zh-TW) and changelog codes
    (zh/tw) and regional suffixes (zh-Hans-sg, zh-Hans-my).
    """
    base = os.path.splitext(fname)[0]  # e.g. "zh-Hans-sg"
    # Strip a trailing regional suffix after a second dash.
    m = re.match(r"^([a-zA-Z]+(-[A-Za-z]+)?)", base)
    core = m.group(1) if m else base
    return normalize_lang(core)


def role_label(role: str) -> str:
    """Human label (already translated) for a role constant."""
    from app.i18n import t

    return {
        ROLE_I18N: t("role.i18n"),
        ROLE_CHANGELOG: t("role.changelog"),
        ROLE_LEGAL: t("role.legal"),
        ROLE_GENERIC_JSON: t("role.generic.json"),
        ROLE_GENERIC_MD: t("role.generic.md"),
    }.get(role, role)


def is_json_role(role: str) -> bool:
    return role in (ROLE_I18N, ROLE_CHANGELOG, ROLE_GENERIC_JSON)


def is_markdown_role(role: str) -> bool:
    return role in (ROLE_LEGAL, ROLE_GENERIC_MD)
