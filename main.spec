# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Get the directory of the spec file
here = os.path.dirname(os.path.abspath(__file__))

# Define the path to EasyOCR models relative to the project root
easyocr_models_path = os.path.join(here, 'easyocr_models')
# Define the path to the src directory
src_path = os.path.join(here, 'src')


a = Analysis(
    ['src/app/main.py'],
    pathex=[here], # Include the current directory in pathex
    binaries=[],
    datas=[
        (easyocr_models_path, 'easyocr_models'), # EasyOCR models
        (src_path, 'src'), # Include the whole src directory
    ],
    hiddenimports=['easyocr'], # Add easyocr as a hidden import
    # ... rest of the file
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='LimbusCalculator', # Renamed executable
    console=True, # Ensure console is enabled for debugging
    # ... rest of the file
)
