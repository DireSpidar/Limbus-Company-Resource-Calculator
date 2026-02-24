import os
import sys
from flask import Flask, jsonify, render_template, request, redirect, url_for

# Path handling for PyInstaller and development
if getattr(sys, 'frozen', False):
    # If the app is bundled by PyInstaller
    template_folder = os.path.join(sys._MEIPASS, 'src', 'app', 'templates')
    # Add project root to path for other imports
    sys.path.append(sys._MEIPASS)
else:
    # Development: Add project root to path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if project_root not in sys.path:
        sys.path.append(project_root)
    template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

app = Flask(__name__, template_folder=template_folder)

# We initialize the tracker outside to be shared, but in a real app, 
# you might use a factory pattern or global object.
# The tracker will be passed in or initialized here.
from src.tracking.progress import ProgressTracker
tracker = ProgressTracker()

@app.route('/')
def home():
    tracker.reload_current_progress() # Ensure tracker has latest data
    
    # We need ego_display_data for the manual update section if we want it to show current levels
    # For now, let's just pass the necessary data.
    ego_display_data = []
    for item in tracker.progress.get('E.G.O.', []):
        ego_display_data.append({
            'id': item.get('id'),
            'current_uptie': item.get('current_uptie')
        })
        
    return render_template('home.html', 
                           ego_display_data=ego_display_data, 
                           all_sinners_data=tracker.sinners)

@app.route('/update_ego_level', methods=['POST'])
def update_ego_level():
    # Security: Validate and sanitize inputs
    ego_id = request.form.get('E.G.O.')
    try:
        new_level = int(request.form.get('new_level', -1))
    except (ValueError, TypeError):
        return "Invalid level", 400

    if ego_id and 0 <= new_level <= 4:
        success = tracker.update_item_level('E.G.O.', ego_id, new_level)
        if success:
            return redirect(url_for('home'))
        else:
            return "Item not found", 404
    return "Invalid request", 400

@app.route('/api/progress')
def api_progress():
    """API endpoint to get the current progress data."""
    # Security: Limit access if needed, but for local app 127.0.0.1 is usually fine.
    return jsonify(tracker.progress)

@app.route('/visualizer')
def visualizer():
    """Renders the progress visualizer page."""
    tracker.reload_current_progress()
    progress_data = tracker.get_sinner_progress()
    return render_template('visualizer.html', progress_data=progress_data)

def run_app():
    # Security: Never use debug=True in production/distributed builds
    # Use 127.0.0.1 to ensure it's only accessible locally.
    host = '127.0.0.1'
    port = 5000
    print(f"Starting Limbus Company Resource Calculator UI on http://{host}:{port}")
    
    try:
        from waitress import serve
        serve(app, host=host, port=port)
    except ImportError:
        # Fallback to Flask's built-in server if waitress is not installed
        app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    run_app()
