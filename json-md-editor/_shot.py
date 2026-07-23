"""Render the main window offscreen and save PNG screenshots (light + dark)."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)
app.setStyle("Fusion")

from app.i18n import set_lang
from app.main_window import MainWindow

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE = os.path.join(HERE, "sample_data")

set_lang("zh-Hans")
mw = MainWindow()
mw.resize(1240, 800)
mw.open_file(os.path.join(SAMPLE, "i18n", "zh-Hans.json"))
# show the JSON preview pane so the render is visible
je = mw.tabs.widget(0)
je.toggle_preview()
mw.show()
app.processEvents()

for mode, name in (("dark", "shot_dark.png"), ("light", "shot_light.png")):
    idx = mw._theme_combo.findData(mode)
    mw._theme_combo.setCurrentIndex(idx)
    app.processEvents()
    app.processEvents()
    pix = mw.grab()
    out = os.path.join(HERE, name)
    pix.save(out)
    print("saved", out, pix.width(), "x", pix.height())

print("DONE")
