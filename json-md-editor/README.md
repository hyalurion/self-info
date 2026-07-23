# JSON & Markdown Editor (self-info Edition)

A **PyQt6**-based desktop application for efficient visual editing and management of **JSON files** and **Markdown legal documents**.
Deeply adapted for the `self-info` site project: recognizes three data roles, supports four interface languages
(Japanese / English / Simplified Chinese / Traditional Chinese), and provides three modern themes (Light / Dark / Follow System).

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
- **UI Preview** (toolbar "Preview" button / click again to switch back to "Edit"): Renders JSON to approximate the site's real presentation, faithfully reproducing `self-info`'s Vue rendering logic:
  - **i18n Content**: Rich-text segments (`text` / `ruby` furigana / `highlight` highlight blocks / `info` info blocks, recursively nestable) / differentiated layouts for various `section` types (Birthday / Language / ACG / Personality / Lucky / Gaming / SNS / Conclusion) / footer / legal cards.
  - **Changelog**: Each `[{version, date, content}]` presented as a card, `content` rendered with Markdown.
  - 300ms debounced auto-re-render during editing; error prompt when JSON is invalid. Preview colors change in real-time with themes (Light / Dark / Follow System).

### Markdown Legal Document Editing
- **Live Preview**: Edit on the left, render on the right (300ms debounce).
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
  interface automatically follows when system light/dark changes. Application shell and Markdown / JSON preview area colors are consistent, theme preference persisted.
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

`requirements.txt` dependencies: `PyQt6>=6.6.0`, `markdown>=3.5.0`

> Note: `main.py` is running with the correct Python interpreter that has `PyQt6` installed.

> Running environment hint (local): `C:\Users\qtequ\.workbuddy\binaries\python\envs\default\Scripts\python.exe`
> (PyQt6 6.11 + markdown 3.10). Start command:
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
│   ├── json_preview.py      # JSON → UI preview (faithfully reproduces Vue's rich-text / section / changelog rendering)
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
