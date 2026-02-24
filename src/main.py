import time
import threading
import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vision.recognizer import Recognizer
from src.tracking.progress import ProgressTracker
from src.app.main import run_app

def recognition_loop(recognizer, tracker, stop_event):
    """The main loop for screen recognition."""
    logger.info("Starting recognition loop... Use the UI to monitor progress.")
    
    while not stop_event.is_set():
        try:
            # Capture the screen
            screen = recognizer.capture_screen()

            # Detect if an upgrade happened
            item_type, item_id, new_level = recognizer.detect_upgrade_event(screen)

            if item_type and item_id and new_level is not None:
                logger.info(f"Detected upgrade: {item_type} {item_id} -> {new_level}")
                tracker.update_item_level(item_type, item_id, new_level)

            # Wait for a bit before the next scan
            # We use a short sleep in a loop to respond quickly to stop_event
            for _ in range(50): # 5 seconds total (50 * 0.1)
                if stop_event.is_set():
                    break
                time.sleep(0.1)

        except Exception as e:
            logger.error(f"Error in recognition loop: {e}")
            time.sleep(10)

    logger.info("Recognition loop stopped.")

def main():
    """Main function to initialize and run the application components."""
    logger.info("Initializing Limbus Company Progress Tracker V2-Win...")

    try:
        # Initialize components
        recognizer = Recognizer()
        tracker = ProgressTracker()
        
        stop_event = threading.Event()

        # Run the Flask app in a separate thread
        flask_thread = threading.Thread(target=run_app, daemon=True)
        flask_thread.start()

        # Start the recognition loop
        # We run this in the main thread so we can catch KeyboardInterrupt easily
        recognition_loop(recognizer, tracker, stop_event)

    except KeyboardInterrupt:
        logger.info("Shutdown requested by user.")
        stop_event.set()
    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
