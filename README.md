# Limbus Company Resource Calculator
Companion app for tracking and visualizing resource costs in Limbus Company.

## Windows Download & Usage Instructions (Recommended)

This application is designed as a "one-and-done" program. You do not need to install Python, Tesseract, or any other third-party utilities to use the Windows version.

### 1. Download the Application
*   Go to the [Releases](https://github.com/DireSpidar/Limbus-Company-Resource-Calculator/releases) page on GitHub.
*   Download the latest `LimbusCalculator.zip` file.
*   Extract the contents of the ZIP file to a folder of your choice.

### 2. Run the Program
*   Double-click on `LimbusCalculator.exe`.
*   A console window will open, and the background screen recognition loop will start.
*   The application will automatically open your web browser to `http://127.0.0.1:5000`.

### 3. How to Use the Tracker
*   **Visualizer:** View your overall progress and costs to reach max level for all E.G.O.s.
*   **Screen Recognition (OCR):** 
    *   Click the **"Toggle OCR"** button in the bottom-right corner of the web interface to start or stop screen monitoring.
    *   While active, the program watches for the E.G.O. upgrade screen in Limbus Company.
    *   When an upgrade is detected, your progress is automatically updated in the tracker and reflected in the visualizer.
*   **Manual Update:** You can also manually update item levels through the web interface if preferred.

---

## Developer Setup (Running from Source)

If you wish to run the application from the source code or contribute:

### 1. Prerequisites
*   Python 3.10 or higher.
*   Standard developer tools (git).

### 2. Installation
1.  Clone the repository:
    ```bash
    git clone https://github.com/DireSpidar/Limbus-Company-Resource-Calculator.git
    cd Limbus-Company-Resource-Calculator
    ```
2.  Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    # Windows:
    .venv\Scripts\activate
    # Linux/macOS:
    source .venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### 3. Run the Application
```bash
python src/main.py
```

### 4. Building the Executable (Windows)
To create a standalone EXE using PyInstaller:
```bash
pyinstaller main.spec
```
The resulting EXE will be located in the `dist/` folder.
