import time
import threading
import sys
import os
import webbrowser

# Ensure the current directory is in the path so we can find 'src'
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.vision.recognizer import Recognizer
from src.tracking.progress import ProgressTracker
from src.app.main import create_app


def recognition_loop(recognizer, tracker):
    """
    Continuous loop that monitors the screen for upgrade events
    when OCR monitoring is enabled in the tracker.
    """
    print("Starting background recognition loop...")

    # Create a mapping from name to ID for E.G.O.s
    ego_name_to_id = {}
    for ego in tracker.progress.get('E.G.O.', []):
        ego_name_to_id[ego['name']] = ego['id']

    # State tracking to avoid spamming the same detection
    # { "E.G.O. ID": level }
    last_detected_levels = {}

    while True:
        try:
            if tracker.ocr_enabled:
                screen = recognizer.capture_screen()
                detections = recognizer.detect_upgrade_event(screen)

                for item_name, new_level, _ in detections:
                    item_id = ego_name_to_id.get(item_name)
                    if item_id:
                        # Check if this is a new detection or a level change
                        if last_detected_levels.get(item_id) != new_level:
                            # Also check tracker's current value to avoid redundant saves
                            current_val = 0
                            for ego in tracker.progress.get('E.G.O.', []):
                                if ego['id'] == item_id:
                                    current_val = ego.get('current_uptie', 0)
                                    break
                            
                            if current_val != new_level:
                                print(f"Detected upgrade: {item_name} ({item_id}) -> Level {new_level}")
                                tracker.update_item_level('E.G.O.', item_id, new_level)
                            
                            # Update local state even if tracker was already correct
                            last_detected_levels[item_id] = new_level

            # Sleep to reduce CPU usage
            time.sleep(1)

        except Exception as e:
            print(f"Recognition loop error: {e}")
            time.sleep(2)


def open_browser():
    """
    Wait briefly for Flask to start, then open the browser.
    """
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:5000")


def main():
    """Main function to initialize and run the application components."""
    print("Initializing Limbus Company Progress Tracker...")

    # Initialize components
    tracker = ProgressTracker()
    
    # Extract E.G.O. names for the recognizer
    ego_names = [ego['name'] for ego in tracker.progress.get('E.G.O.', [])]
    recognizer = Recognizer(ego_names=ego_names)
    
    app = create_app(tracker)

    # Start Flask in a background thread
    flask_thread = threading.Thread(
        target=app.run,
        kwargs={
            "host": "127.0.0.1",
            "port": 5000,
            "debug": False,
            "use_reloader": False
        },
        daemon=True
    )
    flask_thread.start()

    # Automatically open browser for the user
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # Start recognition loop in main thread
    try:
        recognition_loop(recognizer, tracker)
    except KeyboardInterrupt:
        print("Exiting application.")
        sys.exit(0)


if __name__ == "__main__":
    main()