import sys
import time
import threading
import webbrowser


try:
    from src.vision.recognizer import Recognizer
    from src.tracking.progress import ProgressTracker
    from src.app.main import create_app
except Exception as e:
    print("Failed to import application modules.")
    print(f"Error: {e}")
    sys.exit(1)


def recognition_loop(recognizer, tracker, stop_event: threading.Event):
    """
    Continuous loop that monitors the screen for upgrade events
    when OCR monitoring is enabled in the tracker.
    """
    print("Starting background recognition loop...")

    while not stop_event.is_set():
        try:
            if getattr(tracker, "ocr_enabled", False):
                screen = recognizer.capture_screen()
                item_id, new_level, _ = recognizer.detect_upgrade_event(screen)

                if (
                    item_id
                    and item_id != "UNKNOWN_ITEM"
                    and new_level is not None
                    and new_level != "UNKNOWN_LEVEL"
                ):
                    print(f"Detected upgrade: {item_id} -> Level {new_level}")
                    tracker.update_item_level("E.G.O.", item_id, new_level)

        except Exception as e:
            print(f"[Recognition Error] {e}")

        stop_event.wait(1.0)

    print("Recognition loop stopped.")


def run_flask(app):
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
        threaded=True
    )


def main():
    print("Initializing Limbus Company Progress Tracker...")

    stop_event = threading.Event()

    try:
        recognizer = Recognizer()
        tracker = ProgressTracker()
        app = create_app(tracker)

        flask_thread = threading.Thread(
            target=run_flask,
            args=(app,),
            daemon=True
        )
        flask_thread.start()

        ocr_thread = threading.Thread(
            target=recognition_loop,
            args=(recognizer, tracker, stop_event),
            daemon=True
        )
        ocr_thread.start()

        print("Opening web interface...")
        time.sleep(1.5)
        webbrowser.open("http://127.0.0.1:5000")

        print("App is running. Press Ctrl+C to exit.")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nExiting application...")
        stop_event.set()
        time.sleep(0.5)
        sys.exit(0)

    except Exception as e:
        print(f"Fatal error: {e}")
        stop_event.set()
        sys.exit(1)


if __name__ == "__main__":
    main()
