# -*- mode: python ; coding: utf-8 -*-
import os
import sys

here = os.path.dirname(os.path.abspath(sys.argv[0]))
easyocr_models_path = os.path.join(here, 'easyocr_models')
src_path = os.path.join(here, 'src')

a = Analysis(
    ['main_exe.py'],
    pathex=[here],
    binaries=[],
    datas=[
        (easyocr_models_path, 'easyocr_models'),
        (src_path, 'src'),
    ],
    hiddenimports=['easyocr', 'flask', 'pyautogui', 'pygetwindow', 'mss', 'cv2'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LimbusCalculator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LimbusCalculator',
)
