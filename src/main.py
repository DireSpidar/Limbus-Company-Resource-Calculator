import time
import threading
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
    last_detected_levels = {}

    while True:
        if tracker.ocr_enabled:
            # print("OCR Monitoring is active. Capturing screen...") # Too noisy
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
                        
                        # Update local state
                        last_detected_levels[item_id] = new_level
        
        # Sleep to reduce CPU usage. Adjust as needed.
        time.sleep(1)

def main():
    """Main function to initialize and run the application components."""
    print("Initializing Limbus Company Progress Tracker...")

    # Initialize components
    tracker = ProgressTracker()
    
    # Extract E.G.O. names for the recognizer
    ego_names = [ego['name'] for ego in tracker.progress.get('E.G.O.', [])]
    recognizer = Recognizer(ego_names=ego_names)
    
    app = create_app(tracker)

    # Run the Flask app in a separate thread
    # The `daemon=True` flag means the thread will exit when the main program exits.
    flask_thread = threading.Thread(target=app.run, kwargs={'host': '127.0.0.1', 'port': 5000}, daemon=True)
    flask_thread.start()

    # Start the recognition loop in the main thread
    recognition_loop(recognizer, tracker)

    # Keep the main thread alive to allow the Flask app to continue running.
    print("Recognition loop stopped. The web UI is still running. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting application.")
        sys.exit(0)


if __name__ == "__main__":
    main()
