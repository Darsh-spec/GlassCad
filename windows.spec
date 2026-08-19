# -*- mode: python ; coding: utf-8 -*-
import customtkinter
import os

ctk_path = os.path.dirname(customtkinter.__file__)
block_cipher = None

# ---- Main app ----
a1 = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[(ctk_path, "customtkinter")],
    hiddenimports=['bchlib', 'reedsolo', 'cryptography'],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[],
    cipher=block_cipher, noarchive=False,
)
pyz1 = PYZ(a1.pure, a1.zipped_data, cipher=block_cipher)
exe1 = EXE(
    pyz1, a1.scripts, a1.binaries, a1.zipfiles, a1.datas, [],
    name='GlassCAD', debug=False, strip=False, upx=True,
    console=False,
)

# ---- Hologram viewer ----
a2 = Analysis(
    ['gui/hologram/native/native_hologram_process.py'],
    pathex=['gui/hologram/native'],
    binaries=[],
    datas=[('gui/hologram/native/shaders', 'shaders')],
    hiddenimports=['moderngl', 'glcontext', 'PySide6.QtOpenGLWidgets'],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[],
    cipher=block_cipher, noarchive=False,
)
pyz2 = PYZ(a2.pure, a2.zipped_data, cipher=block_cipher)
exe2 = EXE(
    pyz2, a2.scripts, a2.binaries, a2.zipfiles, a2.datas, [],
    name='GlassCAD-Hologram', debug=False, strip=False, upx=True,
    console=False,
)
