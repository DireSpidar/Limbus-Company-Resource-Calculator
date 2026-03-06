import os
import sys
import mss
import numpy as np
import cv2
import easyocr
from PIL import Image

class Recognizer:
    def __init__(self, monitor_number=1):
        self.sct = mss.mss()
        try:
            self.monitor = self.sct.monitors[monitor_number]
        except IndexError:
            print(f"Warning: Monitor {monitor_number} not found. Defaulting to monitor 1.")
            self.monitor = self.sct.monitors[1]

        # Path setup for models and templates
        if getattr(sys, 'frozen', False):
            # If running as a bundled EXE
            self.base_path = sys._MEIPASS
        else:
            # If running from source
            self.base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        self.models_dir = os.path.join(self.base_path, "easyocr_models")
        self.templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        
        # Initialize EasyOCR reader with local models
        # We disable download and point to our local directory
        self.reader = easyocr.Reader(['en'], gpu=False, model_storage_directory=self.models_dir, download_enabled=False)

        # Load upgrade template
        self.upgrade_template_path = os.path.join(self.templates_dir, "upgrade_template.png")
        self.upgrade_template = cv2.imread(self.upgrade_template_path, cv2.IMREAD_COLOR)
        if self.upgrade_template is None:
            print(f"Warning: Could not load upgrade template from {self.upgrade_template_path}.")

        # ROI configurations (Normalized for 1920x1080, will scale if needed)
        # Red Area: Sinner Name and "E.G.O." check
        # Blue Area: Item Name and Level
        self.roi_config = {
            "red_area_sinner": {"top": 0.05, "left": 0.05, "width": 0.3, "height": 0.15},
            "blue_area_item": {"top": 0.6, "left": 0.6, "width": 0.35, "height": 0.3}
        }
        
        self.sinners_path = os.path.join(self.base_path, "src", "data", "sinners.json")
        self.sinners_data = self._load_sinners_data()
        self.sinners_list = [s["name"] for s in self.sinners_data.get("sinners", [])]

    def _load_sinners_data(self):
        import json
        if os.path.exists(self.sinners_path):
            with open(self.sinners_path, 'r', encoding="utf-8") as f:
                return json.load(f)
        return {"sinners": []}

    def _find_ego_id(self, sinner_name, item_name):
        """Maps sinner name and item name to an EGO ID."""
        if not sinner_name or not item_name:
            return None
        
        for sinner in self.sinners_data.get("sinners", []):
            if sinner["name"] == sinner_name:
                ego_names = [ego["name"] for ego in sinner["egos"]]
                best_ego_name = self._find_best_match(item_name, ego_names)
                if best_ego_name:
                    for ego in sinner["egos"]:
                        if ego["name"] == best_ego_name:
                            return ego["id"]
        return None

    def capture_screen(self):
        """Captures the screen and returns a numpy array in BGR format."""
        sct_img = self.sct.grab(self.monitor)
        # Convert to PIL Image then to numpy array (BGR)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    def _clamp_roi_coords(self, img, roi):
        """Calculates pixel coordinates for an ROI and ensures they stay within image bounds."""
        h, w = img.shape[:2]
        
        # If roi uses relative coordinates (0-1), scale them
        if all(v <= 1.0 for v in roi.values()):
            top = int(roi["top"] * h)
            left = int(roi["left"] * w)
            width = int(roi["width"] * w)
            height = int(roi["height"] * h)
        else:
            top, left, width, height = roi["top"], roi["left"], roi["width"], roi["height"]

        bottom = min(top + height, h)
        right = min(left + width, w)
        top = max(0, top)
        left = max(0, left)
        
        return top, left, bottom, right

    def _find_best_match(self, detected_text, options):
        """Finds the best match from a list of options for the detected text."""
        import difflib
        matches = difflib.get_close_matches(detected_text, options, n=1, cutoff=0.6)
        return matches[0] if matches else None

    def detect_upgrade_event(self, screen_capture):
        """
        Detects an upgrade event and extracts sinner, item_name, and new_level.
        """
        if self.upgrade_template is not None:
            result = cv2.matchTemplate(screen_capture, self.upgrade_template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            detection_threshold = 0.8
            if max_val < detection_threshold:
                 return None, None, None
            print(f"Upgrade screen detected (confidence: {max_val:.2f})")
        else:
            # Fallback if no template
            max_loc = (0, 0)

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
            match = self._find_best_match(text, self.sinners_list)
            if match:
                detected_sinner = match

        if not is_ego:
            # Check if we can still find a sinner, maybe it's just missing "E.G.O" text but template matched
            if not detected_sinner:
                return None, None, None

        # 2. Process Blue Area (Item Name + Level)
        blue_roi = self.roi_config["blue_area_item"]
        t, l, b, r = self._clamp_roi_coords(screen_capture, blue_roi)
        blue_img = screen_capture[t:b, l:r]
        blue_results = self.reader.readtext(blue_img, detail=0)

        for text in blue_results:
            # Look for level (usually a digit after some text)
            if any(char.isdigit() for char in text):
                digits = ''.join(filter(str.isdigit, text))
                if digits:
                    detected_level = int(digits)
            else:
                # Assume it's the item name
                if not detected_item or len(text) > len(detected_item):
                    detected_item = text

        if detected_sinner and detected_item:
             # Map detected names to actual EGO ID
             ego_id = self._find_ego_id(detected_sinner, detected_item)
             if ego_id:
                return ego_id, detected_level, max_loc

        return None, None, None



