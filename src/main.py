import time
import threading
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vision.recognizer import Recognizer
from src.tracking.progress import ProgressTracker
from src.app.main import create_app

def main():
    """Main function to initialize and run the application components."""
    print("Initializing Limbus Company Progress Tracker...")

    # Initialize components
    recognizer = Recognizer()
    tracker = ProgressTracker()
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
