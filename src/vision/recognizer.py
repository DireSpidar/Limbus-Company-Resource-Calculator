import numpy as np
import pyautogui
import easyocr
from PIL import Image


class Recognizer:
    def __init__(self):
        print("Loading EasyOCR...")
        self.reader = easyocr.Reader(['en'], gpu=False)
        print("EasyOCR loaded successfully.")

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