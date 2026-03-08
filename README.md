# Limbus Company Resource Calculator

A resource tracking tool for **Limbus Company** that uses **OCR screen recognition** to automatically detect upgrades and update resource progress in real time.

This project was developed for **DEV460**.

---

# Features

- Automatic **OCR detection of upgrades**
- Real-time **resource tracking**
- Simple **web-based interface**
- Toggle OCR monitoring on/off
- Works while the game is running

---

# Requirements

Before running the project you must install:

- Python **3.9+**
- Required Python packages

---

# Installation

## 1. Download the Project

Download the repository:

**Code → Download ZIP**

Extract the folder.

Example folder structure:

Documents
  Limbus-Company-Resource-Calculator


Or clone with Git:

git clone https://github.com/DireSpidar/Limbus-Company-Resource-Calculator.git


---

# 2. Install Dependencies

Open a terminal inside the project folder and run:

pip install -r requirements.txt

If that does not work, install the packages manually:

pip install easyocr pyautogui pillow numpy flask


---

# Running the Application

Start the application with:

python main_exe.py

You should see something like:

Initializing Limbus Company Progress Tracker...
Starting background recognition loop...
Running on http://127.0.0.1:5000


Your browser should open automatically.

If it does not open, go to:

http://127.0.0.1:5000


---

# Using the Tracker

1. Launch the tracker.
2. Start **Limbus Company**.
3. Enable **OCR Monitoring** in the web interface.
4. Play normally.

When upgrade screens appear, the tracker will detect them and update the resource tracker automatically.

---

# Stopping the Program

Return to the terminal window and press:

CTRL + C


---

# Troubleshooting

### Missing Python Module

Example error:

ModuleNotFoundError: No module named 'pyautogui'

Fix by installing the package:

pip install pyautogui


---

### Browser Does Not Open

Open it manually:

http://127.0.0.1:5000


---

### OCR Not Detecting Upgrades

Make sure:

- The game window is visible
- OCR monitoring is enabled
- The upgrade screen is readable

---

# Future Improvements

Planned improvements include:

- One-click `.exe` installer
- Improved OCR accuracy
- GPU acceleration for OCR
- Lower CPU usage
- UI improvements

---

# Contributors

- Joel Koszorus
- DireSpidar

---

# License

This project is intended for educational use.










