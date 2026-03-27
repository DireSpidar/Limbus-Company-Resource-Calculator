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
import math


class Recognizer:
    def __init__(self, ego_names=None):
        print("Loading EasyOCR...")
        self.ego_names = ego_names or []
        # ROI config is kept for future specific crops, but we use full window for now.
        self.roi_config = {
            "item_id_area": {"top": 515, "left": 860, "width": 200, "height": 50},
            "new_level_area": {"top": 575, "left": 860, "width": 150, "height": 30}
        }
        
        # Determine base directory
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        easyocr_model_dir = os.path.join(base_dir, 'easyocr_models')

        if getattr(sys, 'frozen', False):
            application_path = sys._MEIPASS
            bundle_model_dir = os.path.join(application_path, 'easyocr_models')
            self.reader = easyocr.Reader(['en'], model_storage_directory=bundle_model_dir, gpu=False)
        else:
            if os.path.exists(easyocr_model_dir):
                self.reader = easyocr.Reader(['en'], model_storage_directory=easyocr_model_dir, gpu=False)
            else:
                self.reader = easyocr.Reader(['en'], gpu=False)
        print("EasyOCR loaded successfully.")

    def find_game_window(self):
        try:
            windows = gw.getWindowsWithTitle('LimbusCompany')
            if windows:
                win = windows[0]
                return {"top": win.top, "left": win.left, "width": win.width, "height": win.height}
        except Exception as e:
            print(f"Error finding game window: {e}")
        return None

    def capture_screen(self):
        window_rect = self.find_game_window()
        with mss() as sct:
            if window_rect:
                monitor = {"top": window_rect["top"], "left": window_rect["left"], "width": window_rect["width"], "height": window_rect["height"]}
                screenshot = sct.grab(monitor)
            else:
                screenshot = sct.grab(sct.monitors[1])
            return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

    def preprocess_image(self, image):
        open_cv_image = np.array(image)
        open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        contrast = clahe.apply(gray)
        return contrast

    def detect_upgrade_event(self, screen):
        """
        Main entry point for detection. Now returns a LIST of (item_id, level, item_type).
        """
        # We use raw image first as it's often cleaner for standard fonts
        img_np = np.array(screen)
        results = self.reader.readtext(img_np) # detail=1 gives coords
        
        detections = self._process_ocr_results(results)
        
        # If nothing found, try preprocessed
        if not detections:
            proc_img = self.preprocess_image(screen)
            results_proc = self.reader.readtext(proc_img)
            detections = self._process_ocr_results(results_proc)
            
        return detections

    def _get_center(self, bbox):
        """Calculates center of a bounding box [[x,y], [x,y], [x,y], [x,y]]."""
        x_coords = [p[0] for p in bbox]
        y_coords = [p[1] for p in bbox]
        return (sum(x_coords) / 4, sum(y_coords) / 4)

    def _process_ocr_results(self, results):
        """Matches found E.G.O. names to the nearest level indicator."""
        found_names = []
        found_levels = []

        for (bbox, text, conf) in results:
            text_clean = text.strip()
            center = self._get_center(bbox)

            # 1. Look for E.G.O. Names
            for ego_name in self.ego_names:
                if ego_name.lower() in text_clean.lower():
                    found_names.append({"name": ego_name, "center": center})
                    break

            # 2. Look for Levels (I, II, III, IV)
            level = None
            if re.search(r'\b(IV|1V|lV|!V)\b', text_clean): level = 4
            elif re.search(r'\b(III|111|lll|\|\|\|)\b', text_clean): level = 3
            elif re.search(r'\b(II|11|ll|\|\|)\b', text_clean): level = 2
            elif re.search(r'\b(I|1|l|!)\b', text_clean): level = 1
            
            if level:
                found_levels.append({"level": level, "center": center})

        # Match names to closest levels
        final_detections = []
        for name_obj in found_names:
            closest_level = "UNKNOWN_LEVEL"
            min_dist = float('inf')

            for level_obj in found_levels:
                # Euclidean distance
                dist = math.sqrt((name_obj["center"][0] - level_obj["center"][0])**2 + 
                                 (name_obj["center"][1] - level_obj["center"][1])**2)
                
                # In Limbus, the level is usually close horizontally or slightly below/above
                if dist < min_dist:
                    min_dist = dist
                    closest_level = level_obj["level"]

            # Only add if we found a reasonably close level (dist threshold depends on res)
            # 300 is a safe broad threshold for 1080p
            if closest_level != "UNKNOWN_LEVEL" and min_dist < 400:
                final_detections.append((name_obj["name"], closest_level, "E.G.O"))

        return final_detections
