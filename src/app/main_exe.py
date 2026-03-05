from flask import Flask, jsonify
import os
import sys
import shutil

# Add the project root to the Python path to allow imports from other modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.tracking.progress import ProgressTracker  # keep your existing import


def resource_path(relative_path: str) -> str:
    """
    Return an absolute path to a bundled resource.

    - In dev: uses project root (repo root)
    - In PyInstaller EXE: uses the temporary _MEIPASS folder where files are unpacked
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS  # PyInstaller temp folder
    else:
        # repo root: src/app/main_exe.py -> repo_root
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(base_path, relative_path)


def user_data_dir() -> str:
    """
    Return a writable directory for user data on Windows (and a safe fallback elsewhere).
    """
    appdata = os.environ.get("APPDATA")
    if not appdata:
        # fallback for non-Windows or weird environments
        appdata = os.path.expanduser("~")
    folder = os.path.join(appdata, "LimbusCompanyResourceCalculator")
    os.makedirs(folder, exist_ok=True)
    return folder


def user_data_path(filename: str) -> str:
    return os.path.join(user_data_dir(), filename)


def ensure_user_progress_file(user_progress_path: str) -> None:
    """
    Ensure the user_progress.json exists in a writable location.

    If it doesn't exist, try to copy a default from bundled data/user_progress.json.
    If that also doesn't exist, create a minimal empty progress structure.
    """
    if os.path.exists(user_progress_path):
        return

    default_progress_in_bundle = resource_path(os.path.join("data", "user_progress.json"))
    try:
        if os.path.exists(default_progress_in_bundle):
            shutil.copy2(default_progress_in_bundle, user_progress_path)
            return
    except Exception:
        # If copying fails, we’ll fall back to creating a new file
        pass

    # Final fallback: create a basic empty JSON file
    # (Adjust if your ProgressTracker expects a specific structure)
    try:
        with open(user_progress_path, "w", encoding="utf-8") as f:
            f.write("{}")
    except Exception as e:
        raise RuntimeError(f"Could not create user progress file at {user_progress_path}: {e}")


app = Flask(__name__)

# Items are read-only and should be bundled with the EXE
ITEMS_FILE = resource_path(os.path.join("data", "items.json"))

# User progress must be writable and persistent across runs
USER_PROGRESS_FILE = user_data_path("user_progress.json")
ensure_user_progress_file(USER_PROGRESS_FILE)

tracker = ProgressTracker(
    data_file=USER_PROGRESS_FILE,
    items_file=ITEMS_FILE,
)


@app.route("/")
def home():
    # Keep your existing HTML generation behavior
    progress_data = tracker.get_progress_visualization()

    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Limbus Company Progress</title>
    <style>
        body { font-family: sans-serif; margin: 2em; background-color: #f4f4f4; color: #333; }
        h1, h2 { color: #111; }
        .container { background-color: white; padding: 1em 2em; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }
        .progress-bar-container { width: 100%; background-color: #ddd; border-radius: 4px; overflow: hidden; margin-bottom: 12px; }
        .progress-bar { height: 24px; text-align: center; line-height: 24px; color: white; font-weight: 600; }
        .note { font-size: 0.9em; color: #555; margin-top: 1em; }
        code { background: #eee; padding: 2px 6px; border-radius: 4px; }
    </style>
</head>
<body>
  <div class="container">
    <h1>Limbus Company Progress Tracker</h1>
"""

    for item_type, data in progress_data.items():
        # Expecting: data["maxed"], data["total"], data["percentage"]
        # Keep this aligned with your ProgressTracker output.
        html += f"<h2>{item_type.capitalize()}</h2>"
        html += f"<p>Progress: {data.get('maxed', 0)} / {data.get('total', 0)} ({data.get('percentage', 0):.2f}%)</p>"
        html += "<div class='progress-bar-container'>"
        html += (
            f"<div class='progress-bar' "
            f"style='width: {data.get('percentage', 0)}%; background-color: #4CAF50;'>"
            f"{data.get('percentage', 0):.2f}%</div>"
        )
        html += "</div>"

    html += f"""
    <div class="note">
      <p><strong>User data location:</strong> <code>{USER_PROGRESS_FILE}</code></p>
    </div>
  </div>
</body>
</html>
"""
    return html


@app.route("/api/progress")
def api_progress():
    """API endpoint to get the current progress data."""
    return jsonify(tracker.progress)


def run_app():
    print("Starting companion app UI on http://127.0.0.1:5000")

    # Use Waitress for EXE stability on Windows
    from waitress import serve
    serve(app, host="127.0.0.1", port=5000)


if __name__ == "__main__":
    run_app()
