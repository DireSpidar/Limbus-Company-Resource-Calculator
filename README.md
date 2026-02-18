# Limbus-Company-Resource-Calculator
School project for DEV460

## Windows Setup Instructions

To run this application on Windows 10/11, please follow these additional steps:

### 1. Install Tesseract OCR

The application uses Tesseract OCR for image recognition. You need to install Tesseract on your system:

*   Download the installer from the [Tesseract OCR GitHub Releases page](https://github.com/UB-Mannheim/tesseract/wiki). Choose the appropriate `tesseract-ocr-w64-setup-vX.XX.XX.exe` for 64-bit Windows.
*   Run the installer. During installation, ensure you select "Install for all users" and keep the default components. Make a note of the installation directory (e.g., `C:\Program Files\Tesseract-OCR`).

### 2. Set TESSERACT_PATH Environment Variable

The application needs to know where to find the `tesseract.exe` executable.

*   Open the System Properties by searching for "Environment Variables" in the Windows search bar and selecting "Edit the system environment variables".
*   Click on the "Environment Variables..." button.
*   Under "User variables for <YourUsername>" or "System variables" (if you want it available for all users), click "New...".
*   For "Variable name", enter `TESSERACT_PATH`.
*   For "Variable value", enter the full path to the `tesseract.exe` file. For example, if you installed Tesseract to `C:\Program Files\Tesseract-OCR`, the value would be `C:\Program Files\Tesseract-OCR\tesseract.exe`.
*   Click "OK" on all dialogs to save the changes.
*   **Important:** You might need to restart your terminal or IDE for the new environment variable to take effect.

### 3. Activate Virtual Environment (Windows)

To activate the Python virtual environment, use the following command in your terminal (e.g., PowerShell or Command Prompt) from the project root:

```cmd
.venv\Scripts\activate
```

### 4. Run the Application (Windows)

After activating the virtual environment and ensuring Tesseract is configured, you can run the application using:

```cmd
python src\app\main.py
```

The application should then be accessible via `http://127.0.0.1:5000` in your web browser.
