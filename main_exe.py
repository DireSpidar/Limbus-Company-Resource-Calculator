import time
import threading
import sys
import os
import webbrowser

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

    while True:
        try:
            if tracker.ocr_enabled:
                screen = recognizer.capture_screen()
                item_id, new_level, item_type = recognizer.detect_upgrade_event(screen)

                if (
                    item_id
                    and new_level != "UNKNOWN_LEVEL"
                    and item_id != "UNKNOWN_ITEM"
                ):
                    print(f"Detected upgrade: {item_id} -> Level {new_level}")

                    # Default fallback if item_type is missing
                    if not item_type:
                        item_type = "E.G.O"

                    tracker.update_item_level(item_type, item_id, new_level)

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
    recognizer = Recognizer()
    tracker = ProgressTracker()
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