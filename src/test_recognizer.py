import cv2
import os
import sys

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from vision.recognizer import Recognizer

def run_test():
    print("--- Running Recognizer Test ---")

    # Path to the dummy test screenshot
    base_dir = os.path.dirname(__file__)
    test_screenshot_path = os.path.join(base_dir, "vision", "templates", "test_screenshot.png")
    
    # Check if the test screenshot exists
    if not os.path.exists(test_screenshot_path):
        print(f"Error: Test screenshot not found at {test_screenshot_path}")
        print("Please create a 'test_screenshot.png' in src/vision/templates for testing.")
        return

    # Load the test screenshot
    test_screen = cv2.imread(test_screenshot_path)
    if test_screen is None:
        print(f"Error: Could not load image from {test_screenshot_path}. Check file integrity.")
        return

    # Instantiate the Recognizer (monitor_number doesn't matter for test_screen)
    recognizer = Recognizer(monitor_number=1) # Using monitor 1 as default

    # Attempt to detect an upgrade event
    item_id, new_level, match_loc = recognizer.detect_upgrade_event(test_screen)

    if item_id is not None:
        print(f"\nDetection successful!")
        print(f"Detected Item ID: {item_id}")
        print(f"Detected New Level: {new_level}")
        print(f"Match location (top-left corner of template): {match_loc}")
    else:
        print("\nNo upgrade event detected in the test screenshot.")

if __name__ == "__main__":
    # To run this script:
    # 1. Ensure you have the required libraries installed:
    #    pip install -r requirements.txt
    # 2. Place a real 'upgrade_template.png' (small UI element) in src/vision/templates.
    # 3. Place a real 'test_screenshot.png' (full screenshot with the UI element) in src/vision/templates.
    # 4. Adjust the ROI coordinates in recognizer.py's self.roi_config based on your test_screenshot.png.
    # 5. Run this script from the project root: python src/test_recognizer.py
    run_test()
