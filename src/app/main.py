from flask import Flask, jsonify, render_template_string
import sys
import os

# Add the project root to the Python path to allow imports from other modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.tracking.progress import ProgressTracker

app = Flask(__name__)
# Construct path relative to this file to find data files
base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
tracker = ProgressTracker(
    data_file='data/user_progress.json',
    items_file='data/items.json'
)


@app.route('/')
def home():
    # In the future, this will serve a proper HTML file.
    # For now, it's a simple dashboard.
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
            .container { background-color: white; padding: 1em 2em; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .progress-bar-container { width: 100%; background-color: #ddd; border-radius: 4px; }
            .progress-bar { height: 24px; background-color: #4CAF50; text-align: center; color: white; line-height: 24px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Limbus Company Progress Tracker</h1>
    """
    for item_type, data in progress_data.items():
        html += f"<h2>{item_type.capitalize()}</h2>"
        html += f"<p>Progress: {data['maxed']} / {data['total']} ({data['percentage']:.2f}%)</p>"
        html += '<div class="progress-bar-container">'
        html += f'<div class="progress-bar" style="width: {data["percentage"]}%;">{data["percentage"]:.1f}%</div>'
        html += '</div>'
    html += """
        </div>
    </body>
    </html>
    """
    return html

@app.route('/api/progress')
def api_progress():
    """API endpoint to get the current progress data."""
    return jsonify(tracker.progress)

def run_app():
    print("Starting companion app UI on http://127.0.0.1:5000")
    # In a real app, use a production-ready server like waitress or gunicorn
    app.run(host='127.0.0.1', port=5000)

if __name__ == '__main__':
    run_app()
