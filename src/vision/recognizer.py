import os
import sys # Added for PyInstaller check
import mss
import numpy as np
import cv2
import easyocr # Replaced pytesseract
from PIL import Image

class Recognizer:
    def __init__(self, monitor_number=1):
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[monitor_number]

        # Path to the templates directory
        self.templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        
        # Load upgrade template (placeholder)
        self.upgrade_template_path = os.path.join(self.templates_dir, "upgrade_template.png")
        # For a real scenario, this would be a small image of the UI element to detect
        self.upgrade_template = cv2.imread(self.upgrade_template_path, cv2.IMREAD_COLOR)
        if self.upgrade_template is None:
            print(f"Warning: Could not load upgrade template from {self.upgrade_template_path}. Screen recognition might not work as expected.")

        # ROI configurations based on Jonah's descriptions
        # These are rough outlines and need to be tuned for actual game resolution.
        # Red Area: Sinner Name and "E.G.O." check
        # Blue Area: Item Name and Level
        self.roi_config = {
            "red_area_sinner": {"top": 100, "left": 100, "width": 400, "height": 100},
            "blue_area_item": {"top": 500, "left": 800, "width": 600, "height": 200}
        }
        
        # Sinner name mapping to internal IDs if needed, 
        # but the tracker mostly uses EGO names/IDs.
        self.sinners_list = [
            "Yi Sang", "Faust", "Don Quixote", "Ryōshū", "Meursault", 
            "Hong Lu", "Heathcliff", "Ishmael", "Rodion", "Sinclair", 
            "Outis", "Gregor"
        ]

    def _find_best_match(self, detected_text, options):
        """Finds the best match from a list of options for the detected text."""
        import difflib
        matches = difflib.get_close_matches(detected_text, options, n=1, cutoff=0.6)
        return matches[0] if matches else None

    def detect_upgrade_event(self, screen_capture):
        """
        Detects an upgrade event and extracts sinner, item_name, and new_level.
        """
        if self.upgrade_template is None:
            print("Upgrade template not loaded. Still attempting OCR-only detection...")
            # We can still try OCR if template matching fails, 
            # or rely on template matching for robustness.

        # Perform template matching to confirm we are on the right screen
        result = cv2.matchTemplate(screen_capture, self.upgrade_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        detection_threshold = 0.8
        if max_val < detection_threshold:
             # If no template match, we might not be on the upgrade screen
             return None, None, None

        print(f"Upgrade screen detected (confidence: {max_val:.2f})")
            
        # --- OCR Detection ---
        detected_sinner = None
        detected_item = None
        detected_level = None

        # 1. Process Red Area (Sinner + E.G.O. check)
        red_roi = self.roi_config["red_area_sinner"]
        t, l, b, r = self._clamp_roi_coords(screen_capture, red_roi)
        red_img = screen_capture[t:b, l:r]
        red_results = self.reader.readtext(red_img, detail=0)
        
        is_ego = False
        for text in red_results:
            if "E.G.O" in text.upper():
                is_ego = True
            # Check for sinner name
            match = self._find_best_match(text, self.sinners_list)
            if match:
                detected_sinner = match

        if not is_ego:
            print("Detected screen is not an E.G.O. upgrade screen.")
            return None, None, None

        # 2. Process Blue Area (Item Name + Level)
        blue_roi = self.roi_config["blue_area_item"]
        t, l, b, r = self._clamp_roi_coords(screen_capture, blue_roi)
        blue_img = screen_capture[t:b, l:r]
        blue_results = self.reader.readtext(blue_img, detail=0)

        for text in blue_results:
            # Look for level (usually a Roman numeral or number after 'Uptie' or similar)
            # For simplicity, we look for digits or specific keywords.
            if any(char.isdigit() for char in text):
                # Extract digits
                digits = ''.join(filter(str.isdigit, text))
                if digits:
                    detected_level = int(digits)
            else:
                # Assume it's the item name if it's not the level
                if not detected_item or len(text) > len(detected_item):
                    detected_item = text

        print(f"OCR Result - Sinner: {detected_sinner}, Item: {detected_item}, Level: {detected_level}")
        return detected_item, detected_level, max_loc

