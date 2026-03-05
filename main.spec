# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Get the directory of the spec file
here = os.path.dirname(os.path.abspath(sys.argv[0]))

# Define the path to EasyOCR models relative to the project root
easyocr_models_path = os.path.join(here, 'easyocr_models')
# Define the path to the src directory
src_path = os.path.join(here, 'src')


a = Analysis(
    ['src/main.py'],
    pathex=[here], # Include the current directory in pathex
    binaries=[],
    datas=[
        (easyocr_models_path, 'easyocr_models'), # EasyOCR models
        (src_path, 'src'), # Include the whole src directory
    ],
    hiddenimports=['easyocr', 'mss', 'PIL', 'cv2', 'torch', 'torchvision'], # Add dependencies as hidden imports
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LimbusCalculator', # Renamed executable
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, # Ensure console is enabled for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
