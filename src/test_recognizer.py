import os
import sys
from PIL import Image

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vision.recognizer import Recognizer
from src.tracking.progress import ProgressTracker

def run_test():
    print("--- Running Recognizer Test ---")

    # Path to the dummy test screenshot
    base_dir = os.path.dirname(__file__)
    test_screenshot_path = os.path.join(base_dir, "vision", "templates", "test_screenshot.png")
    
    # Check if the test screenshot exists
    if not os.path.exists(test_screenshot_path):
        print(f"Error: Test screenshot not found at {test_screenshot_path}")
        print("Please create a 'test_screenshot.png' in src/vision/templates for testing.")
        # return # Comment out to test without image if needed, but it won't work

    # Instantiate tracker to get ego names
    tracker = ProgressTracker()
    ego_names = [ego['name'] for ego in tracker.progress.get('E.G.O.', [])]

    # Instantiate the Recognizer
    recognizer = Recognizer(ego_names=ego_names)

    if os.path.exists(test_screenshot_path):
        # Load the test screenshot using PIL
        test_screen = Image.open(test_screenshot_path)
        
        # Attempt to detect an upgrade event
        item_id, new_level, item_type = recognizer.detect_upgrade_event(test_screen)

        if item_id != "UNKNOWN_ITEM":
            print(f"\nDetection successful!")
            print(f"Detected Item Name: {item_id}")
            print(f"Detected New Level: {new_level}")
        else:
            print("\nNo upgrade event detected in the test screenshot.")
    else:
        print("Skipping image test as test_screenshot.png is missing.")

if __name__ == "__main__":
    run_test()
