import os
import sys

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from tracking.progress import ProgressTracker

def reset():
    """Main function to reset progress."""
    print("Initializing Progress Tracker for reset...")
    tracker = ProgressTracker()
    tracker.reset_all_progress()

if __name__ == "__main__":
    reset()
