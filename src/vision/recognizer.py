import os
import sys
import numpy as np
import pyautogui
import easyocr
import pygetwindow as gw
import cv2
from PIL import Image
from mss import mss
import re


class Recognizer:
    def __init__(self, ego_names=None):
        print("Loading EasyOCR...")
        self.ego_names = ego_names or []
        # Placeholder for ROI configurations.
        self.roi_config = {
            "item_id_area": {"top": 515, "left": 860, "width": 200, "height": 50},
            "new_level_area": {"top": 575, "left": 860, "width": 150, "height": 30}
        }
        
        # Determine base directory of the project
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        easyocr_model_dir = os.path.join(base_dir, 'easyocr_models')

        if getattr(sys, 'frozen', False):
            # Running as a PyInstaller bundle
            application_path = sys._MEIPASS
            bundle_model_dir = os.path.join(application_path, 'easyocr_models')
            self.reader = easyocr.Reader(['en'], model_storage_directory=bundle_model_dir, gpu=False)
        else:
            # Running as a script (development)
            if os.path.exists(easyocr_model_dir):
                print(f"Using EasyOCR models from: {easyocr_model_dir}")
                self.reader = easyocr.Reader(['en'], model_storage_directory=easyocr_model_dir, gpu=False)
            else:
                print("Local easyocr_models folder not found. EasyOCR will use default storage.")
                self.reader = easyocr.Reader(['en'], gpu=False)
        print("EasyOCR loaded successfully.")

    def find_game_window(self):
        """
        Finds the LimbusCompany window and returns its position and size.
        """
        try:
            windows = gw.getWindowsWithTitle('LimbusCompany')
            if windows:
                win = windows[0]
                return {
                    "top": win.top,
                    "left": win.left,
                    "width": win.width,
                    "height": win.height
                }
        except Exception as e:
            print(f"Error finding game window: {e}")
        return None

    def capture_screen(self):
        """
        Captures the current screen or game window and returns it as an image.
        """
        window_rect = self.find_game_window()
        
        with mss() as sct:
            if window_rect:
                # Capture only the game window
                monitor = {
                    "top": window_rect["top"],
                    "left": window_rect["left"],
                    "width": window_rect["width"],
                    "height": window_rect["height"]
                }
                screenshot = sct.grab(monitor)
            else:
                # Fallback to full screen if window not found
                screenshot = sct.grab(sct.monitors[1])
            
            return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

    def preprocess_image(self, image):
        """
        Applies OpenCV preprocessing to improve OCR accuracy for stylized fonts.
        """
        # Convert PIL to OpenCV (BGR)
        open_cv_image = np.array(image)
        open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)

        # 1. Grayscale
        gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)

        # 2. Resizing (upscaling often helps with small/stylized text)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        # 3. Contrast enhancement (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        contrast = clahe.apply(gray)

        # 4. Thresholding to create a binary image (Black text on White background)
        # adaptiveThreshold helps with varying lighting/backgrounds
        thresh = cv2.adaptiveThreshold(contrast, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        return thresh

    def extract_text(self, image, preprocess=True):
        """
        Uses EasyOCR to extract text from an image, optionally with preprocessing.
        """
        if preprocess:
            processed_image = self.preprocess_image(image)
            results = self.reader.readtext(processed_image, detail=0)
        else:
            if isinstance(image, Image.Image):
                image = np.array(image)
            results = self.reader.readtext(image, detail=0)
            
        return " ".join(results)

    def detect_upgrade_event(self, screen):
        """
        Parses text from the screen to detect upgrade events.
        Tries both raw and preprocessed images for maximum reliability.
        """
        # Try raw extraction first
        text = self.extract_text(screen, preprocess=False)
        item_id, new_level, item_type = self._parse_text_for_upgrade(text)

        # If not found, try with preprocessing
        if item_id == "UNKNOWN_ITEM" or new_level == "UNKNOWN_LEVEL":
            # print("Retrying with image preprocessing...")
            text_proc = self.extract_text(screen, preprocess=True)
            item_id_proc, new_level_proc, _ = self._parse_text_for_upgrade(text_proc)
            
            if item_id == "UNKNOWN_ITEM": item_id = item_id_proc
            if new_level == "UNKNOWN_LEVEL": new_level = new_level_proc

        return item_id, new_level, item_type

    def _parse_text_for_upgrade(self, text):
        """Helper to parse extracted text for E.G.O names and Threadspin levels."""
        item_id = "UNKNOWN_ITEM"
        new_level = "UNKNOWN_LEVEL"
        item_type = "E.G.O"

        # 1. Match E.G.O. Name (Case-insensitive)
        text_lower = text.lower()
        for ego_name in self.ego_names:
            if ego_name.lower() in text_lower:
                item_id = ego_name
                break

        # 2. Detect Threadspin Level (I, II, III, IV)
        # We account for common OCR errors like '1V' for 'IV', 'lI' for 'II', etc.
        # IV patterns: IV, 1V, lV, !V
        if re.search(r'\b(IV|1V|lV|!V|IV)\b', text):
            new_level = 4
        # III patterns: III, 111, lll, |||
        elif re.search(r'\b(III|111|lll|\|\|\|)\b', text):
            new_level = 3
        # II patterns: II, 11, ll, ||
        elif re.search(r'\b(II|11|ll|\|\|)\b', text):
            new_level = 2
        # I patterns: I, 1, l, !
        elif re.search(r'\b(I|1|l|!)\b', text):
            # Level 1 is tricky as it matches many things. 
            # We look for it more strictly if other levels failed.
            new_level = 1

        # 3. Fallback to "Lv. X" or "Level X" if present
        if new_level == "UNKNOWN_LEVEL":
            lv_match = re.search(r'(?:Lv|LV|Level)\.?\s*([1-4])', text, re.IGNORECASE)
            if lv_match:
                new_level = int(lv_match.group(1))

        return item_id, new_level, item_type
