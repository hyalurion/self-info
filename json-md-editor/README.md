# JSON & Markdown Editor (self-info Edition)

A **PyQt6**-based desktop application for efficient visual editing and management of **JSON files** and **Markdown legal documents**.
Deeply adapted for the `self-info` site project: recognizes three data roles, supports four interface languages
(Japanese / English / Simplified Chinese / Traditional Chinese), and provides three modern themes (Light / Dark / Follow System).

Its live preview embeds the **real built site** (the Vue app) via QtWebEngine, so what you see is exactly what
production renders — there is no separate, hand-maintained preview renderer to drift out of sync.

## Core Features

### Project Awareness (Role-aware)
When opening a file, the editor automatically recognizes its semantic role in the `self-info` project based on the path:

| Role | Path Pattern | Editor Capabilities |
| --- | --- | --- |
| **i18n Site Content** | `…/src/data/i18n/<lang>.json` | Rich-text validation, wrap/unwrap/normalize; cross-language consistency check |
| **Changelog** | `…/src/data/changelogs/<lang>.json` | One-click "Add Entry" (version / date / Markdown content) |
| **Legal Documents** | `…/src/data/legal/*.{md}` | Insert privacy policy template by language, auto-numbering `Article N` / `A.` |
| Generic JSON / Markdown | Other paths | Generic editing capabilities |

The status bar displays the current file's "role + language + size", e.g., `i18n Content • Language: Japanese | 1.2 KB`.

### JSON Editing
- **Tree ↔ Text Bidirectional Editing**: Tree structure on the left, text on the right, auto-sync (can be disabled).
- **Node CRUD**: Right-click to add child/sibling nodes or delete; leaf nodes can switch types (string / number / bool / null).
- **Format / Minify / Validate**: One-click beautify, minify, or validate with error line positioning.
- **i18n Rich-text Tools** (Tools menu):
  - Validate schema: Check if rich-text arrays are `{type, content}` (`type ∈ text/info/highlight`).
  - Wrap as rich-text: Convert string fields to `[{"type":"text","content": ...}]`.
  - Unwrap rich-text: Convert single-element rich-text back to plain string.
  - Normalize: Fill missing `type` / `content`.
- **Changelog**: "Add Entry" dialog to input version, date, and content, appended to the array.
- Line numbers, syntax highlighting, find (Ctrl+F).
- **UI Preview** (always visible in a splitter beside the text editor; toolbar "Hide Preview" button collapses it): Renders JSON through the **real site frontend** — an embedded Chromium view (`QWebEngineView`) loads the built Vue app and is fed the edited data, so the preview is pixel-identical to production:
  - **i18n Content**: `header` / `sections` / `footer` rendered by the actual `PageHeader`, `SectionRenderer`, `RichText` and `PageFooter` Vue components (rich-text `text`/`ruby`/`highlight`/`info`/`game-card` segments; all section types — Birthday / Language / ACG / Personality / Lucky / Gaming / SNS / Closing).
  - **Changelog**: each `[{version, date, content}]` rendered as a liquid-glass card with `content` parsed by the site's own `MarkdownRenderer`.
  - 300ms debounced auto re-render while editing; invalid JSON shows the parse error in the preview.

### Markdown Legal Document Editing
- **Live Preview**: Edit on the left, render on the right (300ms debounce) through the site's own `MarkdownRenderer` (marked + DOMPurify) on the production document background.
- **Insert Privacy Policy Template by Language**: Japanese / English / Simplified Chinese / Traditional Chinese, structure consistent with site's `src/data/legal/*`.
- **Auto-numbering**: Legal documents numbered according to site conventions — `Article 1 / Article 2…` (Level 1), `A. / B.` (Level 2), `1.` (Level 3).
- **Table of Contents Navigation**: List all headings, double-click to jump to corresponding line.
- **Word Count**: Chinese character count, character count, estimated word count, line count, estimated page count.
- **Export**: HTML / PDF.
- Syntax highlighting, find.

### Internationalization & Interface
- **Four-language Interface**: Toolbar language selector switches in real-time, menus / toolbar / status bar / dialogs all follow translations.
- Language preference persisted via `QSettings`.
- **Three Themes (Light / Dark / Follow System)**: Toolbar theme selector to switch; "Follow System" reads OS color scheme in real-time,
  interface automatically follows when system light/dark changes. The editor shell follows the selected theme; the live web preview
  always shows the site's own (dark) production theme.
- **Modern Visuals**: Deep purple / light purple background + soft purple accent, rounded controls, thin scrollbars, glass-effect menus/status bar.
- Multi-tab editing, unsaved indicator (`*`); left file browser can switch root directory; save prompt on exit.
- Shortcuts: Ctrl+N New, Ctrl+O Open, Ctrl+S Save, Ctrl+W Close Tab, Ctrl+F Find.

## Installation & Running

Requires Python 3.9+ (verified on Python 3.13). Virtual environment recommended:

```bash
cd json-md-editor
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python main.py
```

`requirements.txt` dependencies: `PyQt6>=6.6.0`, `PyQt6-WebEngine>=6.6.0`, `markdown>=3.5.0`

> The live preview needs the built site. Run `npm run build` in the project root first so that
> `dist/preview.html` exists; the editor serves `dist/` over a local `127.0.0.1` HTTP server and loads it
> in an embedded Chromium view. Set the `SELFINFO_DIST_DIR` environment variable to override the dist location.

> Note: `main.py` is running with the correct Python interpreter that has `PyQt6` installed.

> Running environment hint (local): `C:\Users\qtequ\.workbuddy\binaries\python\envs\default\Scripts\python.exe`
> (PyQt6 6.11 + PyQt6-WebEngine 6.11 + markdown 3.10). Start command:
> ```bash
> python main.py
> ```

## Directory Structure

```
json-md-editor/
├── main.py                  # Entry point: create QApplication and apply theme
├── requirements.txt
├── app/
│   ├── main_window.py       # Main window: menu/toolbar/status bar/language selector/theme selector/consistency check
│   ├── json_editor.py       # JSON editor (role-aware: i18n / changelog / generic) + preview toggle
│   ├── web_preview.py       # Live preview: embeds the real built Vue app (QWebEngineView + localhost server + JS bridge)
│   ├── markdown_editor.py   # Markdown editor (role-aware: legal documents / generic) + live preview
│   ├── file_role.py         # Path → role + language detection
│   ├── i18n.py              # Four-language translation table and t() helper
│   ├── theme.py             # Light/Dark/Follow System three themes (QSS template + palette + preview colors)
│   ├── legal_features.py    # Legal templates, auto-numbering, table of contents, word count
│   ├── code_editor.py       # Code editor with line numbers / highlighting / find
│   ├── highlighters.py      # JSON / Markdown syntax highlighting
│   ├── markdown_converter.py# Markdown → HTML
│   ├── file_explorer.py     # File explorer
│   └── utils.py             # Common utilities
└── sample_data/             # Sample data matching self-info structure
    ├── i18n/{ja,en,zh-Hans,zh-TW}.json
    ├── changelogs/{ja,en,zh,tw}.json
    └── legal/{ja,en,zh-Hans,zh-TW}.md
```

## Usage Tips
- Open any file under `sample_data/` to experience the corresponding role-specific tools; use the file browser to navigate to
  `self-info/src/data/` to directly edit the site's real data.
- After editing i18n multilingual content, use "Tools → Cross-language Consistency Check" and select the `i18n` directory
  to quickly discover missing top-level keys in any language.
- In legal documents, clicking "Auto-numbering" will automatically renumber headings according to the `Article N` / `A.` convention (preserving the preamble section unnumbered).
