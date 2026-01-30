import json
from flask import Flask, jsonify, render_template, request, redirect, url_for
import sys
import os
import requests

# Add the project root to the Python path to allow imports from other modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.tracking.progress import ProgressTracker

def create_app(tracker):
    app = Flask(__name__)
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

    @app.route('/')
    def home():
        ego_display_data = []
        for item in tracker.progress.get('E.G.O.', []): # tracker.progress is the full data loaded from items.json/user_progress.json
            item_id = item.get('id')
            item_name = item.get('name')
            item_grade = item.get('grade')
            max_uptie = item.get('max_uptie')
            current_uptie = item.get('current_uptie') # Get current uptie for proper cost calculation

            if item_id and max_uptie is not None and item_name and item_grade:
                thread, shards = tracker.calculate_ego_upgrade_cost(item_id, max_uptie)
                
                ego_display_data.append({
                    'id': item_id,
                    'name': item_name,
                    'grade': item_grade,
                    'current_uptie': current_uptie,
                    'max_uptie': max_uptie,
                    'cost_to_max': {'thread': thread, 'shards': shards}
                })
            else:
                ego_display_data.append({
                    'id': item_id, 'name': item_name, 'grade': item_grade,
                    'current_uptie': current_uptie, 'max_uptie': max_uptie,
                    'cost_to_max': {'thread': 'N/A', 'shards': 'N/A'}
                })
                    
        return render_template('home.html', ego_display_data=ego_display_data, all_sinners_data=tracker.sinners)

    @app.route('/update_ego_level', methods=['POST'])
    def update_ego_level():
        ego_name = request.form['E.G.O.']
        new_level = int(request.form['new_level'])
        tracker.update_item_level('E.G.O.', ego_name, new_level)
        return redirect(url_for('home'))

    @app.route('/update_items_from_github', methods=['POST'])
    def update_items_from_github():
        github_raw_url = "https://raw.githubusercontent.com/username/repo/branch/src/data/items.json" # Placeholder URL
        try:
            response = requests.get(github_raw_url)
            response.raise_for_status() # Raise an exception for HTTP errors
            new_items_data = response.json()

            # Save to local items.json
            items_file_path = os.path.join(base_dir, tracker.items_file) # Use base_dir and tracker.items_file
            with open(items_file_path, 'w') as f:
                json.dump(new_items_data, f, indent=4)

            # Reload tracker with new data
            tracker.reload_items() # This method needs to be added to ProgressTracker

            print("Successfully updated items.json from GitHub and reloaded tracker.")
            return redirect(url_for('home'))
        except requests.exceptions.RequestException as e:
            print(f"Error fetching items from GitHub: {e}")
            # Optionally, add a flash message for the user
            return redirect(url_for('home'))
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from GitHub response: {e}")
            return redirect(url_for('home'))


    @app.route('/api/progress')
    def api_progress():
        """API endpoint to get the current progress data."""
        return jsonify(tracker.progress)

    @app.route('/visualizer')
    def visualizer():
        """Renders the progress visualizer page."""
        progress_data = tracker.get_sinner_progress()
        return render_template('visualizer.html', progress_data=progress_data)

    return app

if __name__ == '__main__':
    tracker = ProgressTracker()
    app = create_app(tracker)
    print("Starting companion app UI on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000)
