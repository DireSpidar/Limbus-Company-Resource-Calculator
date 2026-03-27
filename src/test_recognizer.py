import os
import sys
from PIL import Image

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vision.recognizer import Recognizer
from src.tracking.progress import ProgressTracker

def run_test():
    print("--- Running Recognizer Test ---")

    # Path to the dummy test screenshot
    base_dir = os.path.dirname(__file__)
    test_screenshot_path = os.path.join(base_dir, "vision", "templates", "test_screenshot.png")
    
    # Instantiate tracker to get sinner data
    tracker = ProgressTracker()

    # Instantiate the Recognizer with sinners data
    recognizer = Recognizer(sinners_data=tracker.sinners.get('sinners', []))

    if os.path.exists(test_screenshot_path):
        # Load the test screenshot using PIL
        test_screen = Image.open(test_screenshot_path)
        
        # Attempt to detect an upgrade event
        sinner, detections = recognizer.detect_upgrade_event(test_screen)

        print(f"Detected Sinner: {sinner or 'None'}")
        if detections:
            print(f"Detections: {detections}")
        else:
            print("No E.G.O.s detected in the test screenshot.")
    else:
        print(f"Skipping image test as {test_screenshot_path} is missing.")

if __name__ == "__main__":
    run_test()
