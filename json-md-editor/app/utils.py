"""General Utilities: File Type Detection, Reading/Writing, Volume Formatting, JSON Validation/Formatting."""

import json
import os


def detect_file_type(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".json", ".jsonl", ".ndjson"):
        return "json"
    if ext in (".md", ".markdown", ".mdx"):
        return "markdown"
    return "unknown"


def read_text(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read()


def write_text(path, text):
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def human_size(num):
    num = max(0, num)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024:
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} PB"


def is_valid_json(text):
    try:
        json.loads(text)
        return True, None
    except json.JSONDecodeError as e:
        return False, f"Line {e.lineno} Column {e.colno}: {e.msg}"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def pretty_json(text):
    return json.dumps(json.loads(text), ensure_ascii=False, indent=2)


def minify_json(text):
    return json.dumps(json.loads(text), ensure_ascii=False, separators=(",", ":"))
