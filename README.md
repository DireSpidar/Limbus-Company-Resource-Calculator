# Limbus Company Resource Calculator
Companion app for tracking and visualizing resource costs in Limbus Company.

## Windows Download & Usage Instructions (Recommended)

This application is designed as a "one-and-done" program. You do not need to install Python or any other third-party utilities to use the Windows version.

### 1. Download the Application
*   Go to the [Releases](https://github.com/DireSpidar/Limbus-Company-Resource-Calculator/releases) page on GitHub.
*   Download the latest `LimbusCalculator.zip` file.
*   Extract the contents of the ZIP file to a folder of your choice.
    *   *Note: If the Releases page is empty, a pre-built version is not yet available. Please see "Building from Source" below.*

### 2. Run the Program
*   Double-click on `LimbusCalculator.exe`.
*   A console window will open, and the background screen recognition loop will start.
*   The application will automatically open your web browser to `http://127.0.0.1:5000`.

### 3. How to Use the Tracker
*   **Visualizer:** View your overall progress and costs to reach max level for all E.G.O.s.
*   **Screen Recognition (OCR):** 
    *   Click the **"Toggle OCR"** button in the bottom-right corner of the web interface to start or stop screen monitoring.
    *   While active, the program watches for the E.G.O. upgrade screen in Limbus Company.
    *   **Red Area (Top-Left):** The program looks here for the Sinner name and the text "E.G.O." to confirm the upgrade screen.
    *   **Blue Area (Bottom-Right):** The program looks here for the Item Name and the new Level.
    *   When an upgrade is detected, your progress is automatically updated in the tracker and reflected in the visualizer.
*   **Manual Update:** You can also manually update item levels through the web interface if preferred.

---

## Developer Setup (Running from Source)

### 1. Prerequisites
*   Python 3.10 or higher.

### 2. Installation
1.  Clone the repository:
    ```bash
    git clone https://github.com/DireSpidar/Limbus-Company-Resource-Calculator.git
    cd Limbus-Company-Resource-Calculator
    ```
2.  Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    .venv\Scripts\activate # Windows
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
To create the standalone EXE:
```bash
pyinstaller main.spec
```
Then, create a ZIP file containing the resulting `LimbusCalculator.exe` from `dist/` and the `data/` folder to ensure persistent progress.
