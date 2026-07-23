"""Headless smoke test for the four reported fixes:
1. polish  2. theme switching  3. i18n coverage  4. open-folder crash.
"""
import os
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

t0 = time.time()
_fail = 0


def check(cond, label):
    global _fail
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        _fail += 1


from PyQt6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)
app.setStyle("Fusion")

import app.theme as theme_mod
from app.theme import apply_theme, get_preview_colors, get_editor_colors
from app.i18n import set_lang, t, SUPPORTED_LANGS
from app.file_explorer import FileExplorer
from app.main_window import MainWindow

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(HERE, "sample_data")

# ---------------------------------------------------------------- 4. crash fix
from PyQt6.QtGui import QFileSystemModel  # must import from QtGui in PyQt6
check(QFileSystemModel is not None, "QFileSystemModel importable from QtGui")

set_lang("zh-Hans")
ex = FileExplorer()
ex.set_root(SAMPLE_DIR)          # this used to crash (bad import in set_root)
check(ex.model is not None, "FileExplorer.set_root builds a model (no crash)")
check(os.path.isdir(SAMPLE_DIR), "sample_data dir exists")

# ---------------------------------------------------------------- 2. theme
apply_theme(app, "zh-Hans", "dark")
ed_dark = get_editor_colors()
apply_theme(app, "zh-Hans", "light")
ed_light = get_editor_colors()
check(ed_dark["gutter_bg"] != ed_light["gutter_bg"], "editor gutter colour differs dark vs light")
check(ed_dark["key"] != ed_light["key"], "syntax key colour differs dark vs light")
# light syntax colours must be dark enough to read on white (rough luminance test)
def lum(hexc):
    hexc = hexc.lstrip("#")
    r, g, b = int(hexc[0:2], 16), int(hexc[2:4], 16), int(hexc[4:6], 16)
    return 0.299 * r + 0.587 * g + 0.114 * b
check(all(lum(ed_light[k]) < 190 for k in ("str", "num", "kw", "key")),
      "light syntax colours are dark enough to read on white")
check(get_preview_colors("light")["bg"] == "#ffffff", "light preview bg is white")

# ---------------------------------------------------------------- 3. i18n
missing = []
new_keys = [
    "explorer.path", "explorer.open.folder", "explorer.open.folder.title",
    "find.placeholder", "find.prev", "find.next", "find.case.tip", "find.close.tip",
    "json.root.object", "json.root.array", "json.newkey", "json.root.nodelete",
    "json.refresh.failed", "json.valid", "json.invalid", "md.template.inserted",
]
for lng in SUPPORTED_LANGS:
    set_lang(lng)
    for k in new_keys:
        val = t(k)
        if val == k:  # unresolved -> key echoed back
            missing.append(f"{lng}:{k}")
check(not missing, "all new i18n keys resolved in every locale" + (f" (missing {missing})" if missing else ""))

# format placeholders work
set_lang("zh-Hans")
check("5" in t("json.newkey").format(n=5), "json.newkey formats {n}")
check("boom" in t("json.refresh.failed").format(err="boom"), "json.refresh.failed formats {err}")

# ---------------------------------------------------------------- full window
set_lang("zh-Hans")
mw = MainWindow()
mw.open_file(os.path.join(SAMPLE_DIR, "i18n", "zh-Hans.json"))
mw.open_file(os.path.join(SAMPLE_DIR, "legal", "zh-Hans.md"))
check(mw.tabs.count() == 2, "opened json + md tabs")

# theme switch cascades without error
for mode in ("light", "dark", "system"):
    idx = mw._theme_combo.findData(mode)
    mw._theme_combo.setCurrentIndex(idx)
check(True, "theme combo cycled light/dark/system without error")

# language switch cascades to explorer + find bar + code editor
prev = ex._path_label.text()
mw._lang_combo.setCurrentIndex(mw._lang_combo.findData("en"))
# explorer inside window
mw.explorer.retranslate_ui()
check(mw.explorer._btn_open.text() == t("explorer.open.folder"), "explorer button retranslated to EN")
# find bar of the json editor
je = mw.tabs.widget(0)
check(je.text_edit.find_widget._edit.placeholderText() == t("find.placeholder"),
      "json editor find bar retranslated to EN")

# code editor retheme runs
je.text_edit.retheme()
check(True, "code editor retheme() ran without error")

print("ELAPSED %.1f s" % (time.time() - t0))
print("ALL_OK" if _fail == 0 else f"FAILURES={_fail}")
sys.exit(1 if _fail else 0)
