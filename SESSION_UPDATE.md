# Session Update - Windows One-and-Done & OCR Refinement

This log details the latest updates made to prepare the Limbus Company Resource Calculator for Windows deployment and refine the EasyOCR implementation.

## 1. Windows "One-and-Done" Implementation
*   **Standalone Executable Configuration:** Updated `main.spec` to use the `onefile` bundle method. This ensures that the application, its models (`easyocr_models/`), and all dependencies (EasyOCR, PyTorch, Flask, etc.) are contained within a single `LimbusCalculator.exe`.
*   **Automatic Browser Launch:** Added `webbrowser.open()` to `src/main.py`. The application now automatically opens the web interface at `http://127.0.0.1:5000` on startup, removing the need for users to manually enter the URL.
*   **Entry Point Correction:** Changed the PyInstaller entry point to `src/main.py` to ensure the background recognition loop starts alongside the web server.

## 2. EasyOCR Logic Refinement (Project Requirements)
*   **Targeted Detection (Red/Blue Areas):** Refined `src/vision/recognizer.py` to use the specific areas described in the project requirements:
    *   **Red Area:** Scans for Sinner names and confirms "E.G.O." text is present to ensure the correct screen is being read.
    *   **Blue Area:** Scans for Item Name and Level (numeric extraction).
*   **Fuzzy Matching:** Implemented a fuzzy matching system for Sinner names to improve OCR reliability against small character errors.
*   **Model Portability:** Verified and updated the logic to load EasyOCR models from the local `easyocr_models/` folder (or the temporary `_MEIPASS` folder when running as an EXE), enabling completely offline operation.

## 3. Documentation & State Management
*   **Simplified README:** Replaced complex Tesseract/Environment Variable instructions with a 3-step guide for non-technical users.
*   **Progress Reset:** Confirmed that `src/data/user_progress.json` is initialized with all current uptie levels at `0` for all E.G.O.s and identities.
*   **Dependency Cleanup:** Removed Tesseract-related instructions as EasyOCR is now the sole engine.

## 4. Modified Files
*   `main.spec`
*   `README.md`
*   `src/main.py`
*   `src/vision/recognizer.py`
*   `src/data/user_progress.json`
