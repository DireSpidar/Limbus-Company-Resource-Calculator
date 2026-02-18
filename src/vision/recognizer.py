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
        if getattr(sys, 'frozen', False):
            # Running as a PyInstaller bundle
            application_path = sys._MEIPASS
            easyocr_model_dir = os.path.join(application_path, 'easyocr_models')
            # Ensure models are copied to easyocr_models during PyInstaller build
            self.reader = easyocr.Reader(['en'], model_storage_directory=easyocr_model_dir, download_iter=0)
        else:
            # Running as a script (development)
            self.reader = easyocr.Reader(['en'], download_iter=0) # download_iter=0 prevents automatic downloads if not found

    def capture_screen(self):
        """Captures the screen and returns it as an OpenCV-compatible BGR NumPy array."""
        sct_img = self.sct.grab(self.monitor)
        img_rgba = np.array(sct_img)
        img_bgr = cv2.cvtColor(img_rgba, cv2.COLOR_RGBA2BGR)
        return img_bgr

    def _clamp_roi_coords(self, image, roi_coords):
        """Clamps ROI coordinates to image boundaries."""
        screen_height, screen_width = image.shape[:2] # Handle both BGR and grayscale images
        top = max(0, min(roi_coords["top"], screen_height))
        left = max(0, min(roi_coords["left"], screen_width))
        bottom = max(0, min(roi_coords["top"] + roi_coords["height"], screen_height))
        right = max(0, min(roi_coords["left"] + roi_coords["width"], screen_width))
        return top, left, bottom, right

    def detect_upgrade_event(self, screen_capture):
        """
        Detects an upgrade event and extracts item_id and new_level.
        """
        if self.upgrade_template is None:
            print("Upgrade template not loaded. Cannot detect upgrade events.")
            return None, None, None

        # Perform template matching
        result = cv2.matchTemplate(screen_capture, self.upgrade_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # Define a threshold for detection confidence
        # This threshold needs to be tuned based on actual game UI and template.
        detection_threshold = 0.8

        if max_val >= detection_threshold:
            print(f"Upgrade event detected with confidence: {max_val:.2f}")
            
            # --- Optical Character Recognition (OCR) using EasyOCR ---
            # These ROIs are placeholders and need to be precisely defined
            # based on the game's UI relative to the detected template location.
            item_id = "UNKNOWN_ITEM"
            new_level = "UNKNOWN_LEVEL"

            # Process Item ID area
            item_id_roi_coords = self.roi_config["item_id_area"]
            top, left, bottom, right = self._clamp_roi_coords(screen_capture, item_id_roi_coords)

            if bottom > top and right > left:
                item_id_image_cv2 = screen_capture[top:bottom, left:right]
                # EasyOCR can directly take a NumPy array (OpenCV image)
                item_id_results = self.reader.readtext(item_id_image_cv2, detail=0)
                if item_id_results:
                    item_id = item_id_results[0].strip() # Assuming the first detected text is the item ID
                print(f"OCR detected Item ID: {item_id}")

            # Process New Level area
            new_level_roi_coords = self.roi_config["new_level_area"]
            top, left, bottom, right = self._clamp_roi_coords(screen_capture, new_level_roi_coords)

            if bottom > top and right > left:
                new_level_image_cv2 = screen_capture[top:bottom, left:right]
                new_level_results = self.reader.readtext(new_level_image_cv2, detail=0)
                if new_level_results:
                    # Attempt to extract a number for the level
                    level_text = new_level_results[0].strip()
                    try:
                        new_level = int(level_text)
                    except ValueError:
                        new_level = "UNKNOWN_LEVEL" # Or handle as string if non-numeric
                print(f"OCR detected New Level: {new_level}")

            return item_id, new_level, max_loc # Returning max_loc for further analysis if needed
        else:
            # print(f"No upgrade event detected. Max confidence: {max_val:.2f}")
            return None, None, None
