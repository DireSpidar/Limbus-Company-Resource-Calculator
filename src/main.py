import time
import threading
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vision.recognizer import Recognizer
from src.tracking.progress import ProgressTracker
from src.app.main import run_app

def recognition_loop(recognizer, tracker):
    """The main loop for screen recognition."""
    print("Starting recognition loop... Press Ctrl+C to stop.")
    while True:
        try:
            # Capture the screen
            screen = recognizer.capture_screen()

            # Detect if an upgrade happened
            item_type, item_id, new_level = recognizer.detect_upgrade_event(screen)

            if item_type and item_id and new_level is not None:
                print(f"Detected upgrade for {item_type} {item_id} to level {new_level}")
                tracker.update_item_level(item_type, item_id, new_level)

            # Wait for a bit before the next scan to avoid high CPU usage
            time.sleep(5)  # 5 seconds polling interval

        except KeyboardInterrupt:
            print("Stopping recognition loop.")
            break
        except Exception as e:
            print(f"An error occurred in the recognition loop: {e}")
            time.sleep(10)  # Wait longer after an error

def main():
    """Main function to initialize and run the application components."""
    print("Initializing Limbus Company Progress Tracker...")

    # Initialize components
    recognizer = Recognizer()
    tracker = ProgressTracker()

    # Run the Flask app in a separate thread
    # The `daemon=True` flag means the thread will exit when the main program exits.
    flask_thread = threading.Thread(target=run_app, daemon=True)
    flask_thread.start()

    # Start the recognition loop in the main thread
    recognition_loop(recognizer, tracker)


if __name__ == "__main__":
    main()
