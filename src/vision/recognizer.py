import os
import mss
import numpy as np
import cv2
import pytesseract
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
        
        # Configure Tesseract path if it's not in your system's PATH
        # Configure Tesseract path if it's not in your system's PATH
        tesseract_path = os.environ.get("TESSERACT_PATH")
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        # Example for Linux: pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

    def capture_screen(self):
        """Captures the screen and returns it as an OpenCV-compatible BGR NumPy array."""
        sct_img = self.sct.grab(self.monitor)
        img_rgba = np.array(sct_img)
        img_bgr = cv2.cvtColor(img_rgba, cv2.COLOR_RGBA2BGR)
        return img_bgr

    def _convert_cv2_to_pil(self, cv2_image):
        """Converts an OpenCV BGR image to a PIL Image."""
        rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_image)

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
            
            # --- Optical Character Recognition (OCR) ---
            # These ROIs are placeholders and need to be precisely defined
            # based on the game's UI relative to the detected template location.
            item_id = "UNKNOWN_ITEM"
            new_level = "UNKNOWN_LEVEL"

            # Example of how to crop and OCR for item_id (placeholder)
            # You would adjust the ROI based on max_loc and template dimensions
            item_id_roi_coords = self.roi_config["item_id_area"]
            
            # Ensure ROI coordinates are within screen_capture bounds
            top = item_id_roi_coords["top"]
            left = item_id_roi_coords["left"]
            bottom = top + item_id_roi_coords["height"]
            right = left + item_id_roi_coords["width"]

            # Clamp coordinates to image boundaries
            screen_height, screen_width, _ = screen_capture.shape
            top = max(0, min(top, screen_height))
            left = max(0, min(left, screen_width))
            bottom = max(0, min(bottom, screen_height))
            right = max(0, min(right, screen_width))
            
            if bottom > top and right > left:
                item_id_image = screen_capture[top:bottom, left:right]
                pil_item_id_image = self._convert_cv2_to_pil(item_id_image)
                item_id = pytesseract.image_to_string(pil_item_id_image, config='--psm 7').strip()
                print(f"OCR detected Item ID: {item_id}")

            # Example for new_level (placeholder)
            new_level_roi_coords = self.roi_config["new_level_area"]

            top = new_level_roi_coords["top"]
            left = new_level_roi_coords["left"]
            bottom = top + new_level_roi_coords["height"]
            right = left + new_level_roi_coords["width"]

            screen_height, screen_width, _ = screen_capture.shape
            top = max(0, min(top, screen_height))
            left = max(0, min(left, screen_width))
            bottom = max(0, min(bottom, screen_height))
            right = max(0, min(right, screen_width))

            if bottom > top and right > left:
                new_level_image = screen_capture[top:bottom, left:right]
                pil_new_level_image = self._convert_cv2_to_pil(new_level_image)
                new_level = pytesseract.image_to_string(pil_new_level_image, config='--psm 7').strip()
                print(f"OCR detected New Level: {new_level}")

            return item_id, new_level, max_loc # Returning max_loc for further analysis if needed
        else:
            # print(f"No upgrade event detected. Max confidence: {max_val:.2f}")
            return None, None, None
