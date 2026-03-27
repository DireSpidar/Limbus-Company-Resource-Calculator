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
        # Convert to grayscale and upscale significantly to help with tiny/stylized level text
        open_cv_image = np.array(image)
        open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_LANCZOS4)
        # Apply sharpening to make stylized fonts clearer
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(gray, -1, kernel)
        return sharpened

    def detect_upgrade_event(self, screen):
        img_np = np.array(screen)
        results = self.reader.readtext(img_np)
        detections = self._process_ocr_results(results)
        
        if not detections:
            # print("No detections in raw image, trying preprocessed...")
            proc_img = self.preprocess_image(screen)
            results_proc = self.reader.readtext(proc_img)
            detections = self._process_ocr_results(results_proc)
            
        return detections

    def _get_center(self, bbox):
        x_coords = [p[0] for p in bbox]
        y_coords = [p[1] for p in bbox]
        return (sum(x_coords) / 4, sum(y_coords) / 4)

    def _process_ocr_results(self, results):
        found_items = []
        
        # Level Patterns (I, II, III, IV)
        lvl_map = {
            r'(IV|1V|lV|!V)': 4,
            r'(III|111|lll|\|\|\|)': 3,
            r'(II|11|ll|\|\|)': 2,
            r'(I|1|l|!)': 1
        }

        # First pass: find all E.G.O. names
        egos_on_screen = []
        for (bbox, text, conf) in results:
            text_clean = text.strip()
            for ego_name in self.ego_names:
                if ego_name.lower() in text_clean.lower():
                    egos_on_screen.append({
                        "name": ego_name,
                        "center": self._get_center(bbox),
                        "text": text_clean
                    })
                    break

        # Second pass: for each E.G.O., find the most likely level
        for ego in egos_on_screen:
            detected_level = None
            
            # 1. Check same text block
            for pattern, val in lvl_map.items():
                if re.search(pattern, ego["text"]):
                    detected_level = val
                    break
            
            # 2. Look for nearest level indicator
            if not detected_level:
                min_dist = 600 # Broad radius
                for (bbox, text, conf) in results:
                    text_clean = text.strip()
                    for pattern, val in lvl_map.items():
                        if re.search(pattern, text_clean):
                            dist = math.sqrt((ego["center"][0] - self._get_center(bbox)[0])**2 + 
                                             (ego["center"][1] - self._get_center(bbox)[1])**2)
                            if dist < min_dist:
                                min_dist = dist
                                detected_level = val
            
            if detected_level:
                found_items.append((ego["name"], detected_level, "E.G.O"))

        return found_items
