import os
import sys
import numpy as np
import pyautogui
import easyocr
from PIL import Image


class Recognizer:
    def __init__(self):
        print("Loading EasyOCR...")
        self.reader = easyocr.Reader(['en'], gpu=False)
        print("EasyOCR loaded successfully.")
        
        # Placeholder for ROI configurations.
        # In a real application, this would be loaded from a config file (e.g., JSON, YAML)
        # and would contain coordinates for various UI elements based on monitor resolution.
        self.roi_config = {
            "item_id_area": {"top": 515, "left": 860, "width": 200, "height": 50},
            "new_level_area": {"top": 575, "left": 860, "width": 150, "height": 30}
        }
        
        # Initialize EasyOCR reader
        # For bundled application, models need to be included in the bundle.
        # For development, easyocr will download models to its default location (~/.EasyOCR/model)
        
        # Determine base directory of the project
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        easyocr_model_dir = os.path.join(base_dir, 'easyocr_models')

        if getattr(sys, 'frozen', False):
            # Running as a PyInstaller bundle
            application_path = sys._MEIPASS
            bundle_model_dir = os.path.join(application_path, 'easyocr_models')
            self.reader = easyocr.Reader(['en'], model_storage_directory=bundle_model_dir)
        else:
            # Running as a script (development)
            # Use the local easyocr_models folder if it exists
            if os.path.exists(easyocr_model_dir):
                print(f"Using EasyOCR models from: {easyocr_model_dir}")
                self.reader = easyocr.Reader(['en'], model_storage_directory=easyocr_model_dir)
            else:
                print("Local easyocr_models folder not found. EasyOCR will use default storage.")
                self.reader = easyocr.Reader(['en'])

    def capture_screen(self):
        """
        Captures the current screen and returns it as an image.
        """
        screenshot = pyautogui.screenshot()
        return screenshot

    def extract_text(self, image):
        """
        Uses EasyOCR to extract text from an image.
        """
        if isinstance(image, Image.Image):
            image = np.array(image)

        results = self.reader.readtext(image, detail=0)
        return " ".join(results)

    def detect_upgrade_event(self, screen):
        """
        Example placeholder logic:
        - Reads text from the screen
        - Tries to detect item + level
        - Returns (item_id, new_level, item_type)

        Replace this parsing logic with your actual game-specific logic.
        """
        text = self.extract_text(screen)
        print(f"OCR Text: {text}")

        # Example placeholder parsing logic
        item_id = "UNKNOWN_ITEM"
        new_level = "UNKNOWN_LEVEL"
        item_type = "E.G.O"

        # Example:
        # if "Level 10" in text:
        #     item_id = "Sample Item"
        #     new_level = 10

        return item_id, new_level, item_type
