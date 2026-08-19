"""
Standalone native process: reads the real result JSON and opens a PySide6 +
ModernGL window rendering the hologram. Fully native GPU rendering -- no
HTML, no browser, no WebView. Runs as its own OS process so it never
conflicts with the main CustomTkinter app's event loop.

Usage: python3 native_hologram_process.py <path_to_result.json>
"""
import sys
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # so `from renderer import ...` resolves

from PySide6.QtWidgets import QApplication, QMainWindow
from hologram_view import HologramView


def main():
    if len(sys.argv) < 2:
        print("Usage: native_hologram_process.py <result.json>")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        data = json.load(f)

    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("GlassCAD — Hologram View")
    window.resize(1100, 750)
    window.setStyleSheet("background-color: #050608;")

    view = HologramView(data)
    window.setCentralWidget(view)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()