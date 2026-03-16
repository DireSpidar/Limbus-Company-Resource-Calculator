import json
import sys
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template, request, redirect, url_for

from src.tracking.progress import ProgressTracker


def resource_path(*parts) -> Path:
    """
    Return a path that works both in development and in a PyInstaller build.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = Path(__file__).resolve().parents[2]
    return base.joinpath(*parts)


def create_app(tracker):
    templates_dir = resource_path("src", "app", "templates")
    static_dir = resource_path("src", "app", "static")

    app = Flask(
        __name__,
        template_folder=str(templates_dir),
        static_folder=str(static_dir)
    )

    @app.route("/")
    def home():
        tracker.reload_current_progress()
        ego_display_data = []

        for item in tracker.progress.get("E.G.O.", []):
            item_id = item.get("id")
            item_name = item.get("name")
            item_grade = item.get("grade")
            max_uptie = item.get("max_uptie")
            current_uptie = item.get("current_uptie")

            if item_id and max_uptie is not None and item_name and item_grade:
                thread, shards = tracker.calculate_ego_upgrade_cost(item_id, max_uptie)

                ego_display_data.append({
                    "id": item_id,
                    "name": item_name,
                    "grade": item_grade,
                    "current_uptie": current_uptie,
                    "max_uptie": max_uptie,
                    "cost_to_max": {"thread": thread, "shards": shards}
                })
            else:
                ego_display_data.append({
                    "id": item_id,
                    "name": item_name,
                    "grade": item_grade,
                    "current_uptie": current_uptie,
                    "max_uptie": max_uptie,
                    "cost_to_max": {"thread": "N/A", "shards": "N/A"}
                })

        return render_template(
            "home.html",
            ego_display_data=ego_display_data,
            all_sinners_data=tracker.sinners
        )

    @app.route("/update_ego_level", methods=["POST"])
    def update_ego_level():
        ego_name = request.form.get("E.G.O.")
        new_level_raw = request.form.get("new_level")

        if not ego_name or not new_level_raw:
            return redirect(url_for("home"))

        try:
            new_level = int(new_level_raw)
        except ValueError:
            return redirect(url_for("home"))

        tracker.update_item_level("E.G.O.", ego_name, new_level)
        return redirect(url_for("home"))

    @app.route("/update_items_from_github", methods=["POST"])
    def update_items_from_github():
        github_raw_url = "https://raw.githubusercontent.com/username/repo/branch/src/data/items.json"

        try:
            response = requests.get(github_raw_url, timeout=10)
            response.raise_for_status()
            new_items_data = response.json()

            items_file_path = resource_path("src", "data", "items.json")
            with open(items_file_path, "w", encoding="utf-8") as f:
                json.dump(new_items_data, f, indent=4, ensure_ascii=False)

            if hasattr(tracker, "reload_items"):
                tracker.reload_items()

            print("Successfully updated items.json from GitHub and reloaded tracker.")
            return redirect(url_for("home"))

        except requests.exceptions.RequestException as e:
            print(f"Error fetching items from GitHub: {e}")
            return redirect(url_for("home"))

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from GitHub response: {e}")
            return redirect(url_for("home"))

        except Exception as e:
            print(f"Unexpected update error: {e}")
            return redirect(url_for("home"))

    @app.route("/api/progress")
    def api_progress():
        return jsonify(tracker.progress)

    @app.route("/api/ocr_status")
    def get_ocr_status():
        return jsonify({"enabled": tracker.ocr_enabled})

    @app.route("/api/toggle_ocr", methods=["POST"])
    def toggle_ocr():
        tracker.ocr_enabled = not tracker.ocr_enabled
        print(f"OCR Monitoring {'enabled' if tracker.ocr_enabled else 'disabled'}.")
        return jsonify({"enabled": tracker.ocr_enabled})

    @app.route("/visualizer")
    def visualizer():
        tracker.reload_current_progress()
        progress_data = tracker.get_sinner_progress()
        return render_template("visualizer.html", progress_data=progress_data)

    return app


if __name__ == "__main__":
    tracker = ProgressTracker()
    app = create_app(tracker)
    print("Starting companion app UI on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
