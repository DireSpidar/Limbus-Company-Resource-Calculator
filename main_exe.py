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
    
    # Create a mapping from (sinner_name, ego_name) to ID for E.G.O.s
    ego_map = {}
    for sinner in tracker.sinners.get('sinners', []):
        s_name = sinner['name']
        for ego in sinner['egos']:
            ego_map[(s_name, ego['name'])] = ego['id']

    # State tracking to avoid spamming the same detection
    last_detected_levels = {}

    while True:
        try:
            if tracker.ocr_enabled:
                screen = recognizer.capture_screen()
                if screen:
                    sinner_name, detections = recognizer.detect_upgrade_event(screen)

                    if detections:
                        print(f"OCR Detections on screen (Sinner: {sinner_name or 'Unknown'}): {detections}")

                    for ego_name, new_level, _ in detections:
                        # If we have a detected sinner, use it to get the unique ID
                        item_id = None
                        if sinner_name:
                            item_id = ego_map.get((sinner_name, ego_name))
                        
                        if not item_id:
                            # Fallback: check if the ego name is unique across all sinners
                            possible_ids = [i_d for (s_n, e_n), i_d in ego_map.items() if e_n == ego_name]
                            if len(possible_ids) == 1:
                                item_id = possible_ids[0]
                            elif len(possible_ids) > 1:
                                # Don't update if we can't be sure which sinner it belongs to
                                if not sinner_name:
                                    print(f"Ambiguous EGO '{ego_name}' detected. Need Sinner detection to update.")
                                continue
                        
                        if item_id:
                            # Check if this is a new detection or a level change
                            if last_detected_levels.get(item_id) != new_level:
                                # Get current value from tracker
                                current_val = 0
                                for ego in tracker.progress.get('E.G.O.', []):
                                    if ego['id'] == item_id:
                                        current_val = ego.get('current_uptie', 0)
                                        break
                                
                                if current_val != new_level:
                                    print(f"Detected upgrade: {ego_name} for {sinner_name or 'Unknown'} ({item_id}) -> Level {new_level}")
                                    tracker.update_item_level('E.G.O.', item_id, new_level)
                                
                                # Update local state
                                last_detected_levels[item_id] = new_level
                else:
                    # No screen captured (maybe window minimized)
                    pass
        except Exception as e:
            print(f"Error in recognition loop: {e}")
        
        # Sleep to reduce CPU usage.
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
    
    # Initialize Recognizer with full sinners data for Sinner-aware detection
    recognizer = Recognizer(sinners_data=tracker.sinners.get('sinners', []))
    
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
