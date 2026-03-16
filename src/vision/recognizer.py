
import json
import sys
from pathlib import Path

import cv2
import easyocr
import mss
import numpy as np


def resource_path(*parts) -> Path:
    """
    Return a path that works both in development and in a PyInstaller build.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = Path(__file__).resolve().parents[2]
    return base.joinpath(*parts)


class Recognizer:
    def __init__(self, monitor_number: int = 1):
        self.sct = mss.mss()

        try:
            self.monitor = self.sct.monitors[monitor_number]
        except IndexError:
            print(f"Warning: Monitor {monitor_number} not found. Defaulting to monitor 1.")
            self.monitor = self.sct.monitors[1]

        self.models_dir = resource_path("easyocr_models")
        self.templates_dir = resource_path("src", "vision", "templates")
        self.sinners_path = resource_path("src", "data", "sinners.json")

        try:
            self.reader = easyocr.Reader(
                ["en"],
                gpu=False,
                model_storage_directory=str(self.models_dir),
                download_enabled=False
            )
        except Exception as e:
            print("Failed to initialize EasyOCR.")
            print("Make sure the EasyOCR model files are bundled in 'easyocr_models'.")
            raise RuntimeError(f"EasyOCR initialization failed: {e}") from e

        self.upgrade_template_path = self.templates_dir / "upgrade_template.png"
        self.upgrade_template = cv2.imread(str(self.upgrade_template_path), cv2.IMREAD_COLOR)
        if self.upgrade_template is None:
            print(f"Warning: Could not load upgrade template from {self.upgrade_template_path}")

        self.roi_config = {
            "red_area_sinner": {"top": 0.05, "left": 0.05, "width": 0.30, "height": 0.15},
            "blue_area_item": {"top": 0.60, "left": 0.60, "width": 0.35, "height": 0.30},
        }

        self.sinners_data = self._load_sinners_data()
        self.sinners_list = [s["name"] for s in self.sinners_data.get("sinners", [])]

    def _load_sinners_data(self):
        if self.sinners_path.exists():
            with open(self.sinners_path, "r", encoding="utf-8") as f:
                return json.load(f)

        print(f"Warning: sinners.json not found at {self.sinners_path}")
        return {"sinners": []}

    def _find_best_match(self, detected_text, options):
        import difflib

        if not detected_text or not options:
            return None

        matches = difflib.get_close_matches(detected_text, options, n=1, cutoff=0.6)
        return matches[0] if matches else None

    def _find_ego_id(self, sinner_name, item_name):
        if not sinner_name or not item_name:
            return None

        for sinner in self.sinners_data.get("sinners", []):
            if sinner.get("name") == sinner_name:
                ego_names = [ego.get("name") for ego in sinner.get("egos", [])]
                best_ego_name = self._find_best_match(item_name, ego_names)
                if best_ego_name:
                    for ego in sinner.get("egos", []):
                        if ego.get("name") == best_ego_name:
                            return ego.get("id")

        return None

    def capture_screen(self):
        sct_img = self.sct.grab(self.monitor)
        img = np.array(sct_img)[:, :, :3]
        return img

    def _clamp_roi_coords(self, img, roi):
        h, w = img.shape[:2]

        if all(v <= 1.0 for v in roi.values()):
            top = int(roi["top"] * h)
            left = int(roi["left"] * w)
            width = int(roi["width"] * w)
            height = int(roi["height"] * h)
        else:
            top = int(roi["top"])
            left = int(roi["left"])
            width = int(roi["width"])
            height = int(roi["height"])

        bottom = min(top + height, h)
        right = min(left + width, w)
        top = max(0, top)
        left = max(0, left)

        return top, left, bottom, right

    def _preprocess_for_ocr(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    def detect_upgrade_event(self, screen_capture):
        max_loc = (0, 0)

        if self.upgrade_template is not None:
            result = cv2.matchTemplate(screen_capture, self.upgrade_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            detection_threshold = 0.8

            if max_val < detection_threshold:
                return None, None, None

            print(f"Upgrade screen detected (confidence: {max_val:.2f})")

        detected_sinner = None
        detected_item = None
        detected_level = None

        red_roi = self.roi_config["red_area_sinner"]
        t, l, b, r = self._clamp_roi_coords(screen_capture, red_roi)
        red_img = screen_capture[t:b, l:r]
        red_img = self._preprocess_for_ocr(red_img)

        red_results = self.reader.readtext(red_img, detail=0)
        is_ego = False

        for text in red_results:
            normalized = str(text).strip()

            if "E.G.O" in normalized.upper() or "EGO" in normalized.upper():
                is_ego = True

            match = self._find_best_match(normalized, self.sinners_list)
            if match:
                detected_sinner = match

        if not is_ego and not detected_sinner:
            return None, None, None

        blue_roi = self.roi_config["blue_area_item"]
        t, l, b, r = self._clamp_roi_coords(screen_capture, blue_roi)
        blue_img = screen_capture[t:b, l:r]
        blue_img = self._preprocess_for_ocr(blue_img)

        blue_results = self.reader.readtext(blue_img, detail=0)

        for text in blue_results:
            normalized = str(text).strip()

            if any(char.isdigit() for char in normalized):
                digits = "".join(filter(str.isdigit, normalized))
                if digits:
                    try:
                        detected_level = int(digits)
                    except ValueError:
                        pass
            else:
                if not detected_item or len(normalized) > len(detected_item):
                    detected_item = normalized

        if detected_sinner and detected_item:
            ego_id = self._find_ego_id(detected_sinner, detected_item)
            if ego_id:
                return ego_id, detected_level, max_loc

        return None, None, None


