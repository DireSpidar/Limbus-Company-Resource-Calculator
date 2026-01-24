import json
import os

class ProgressTracker:
    def __init__(self, data_file='data/user_progress.json', items_file='data/items.json'):
        self.data_file = data_file
        self.items_file = items_file
        self.progress = self.load_progress()

    def load_progress(self):
        """Loads user progress from a file, or initializes it from the base items file."""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                print("Loading existing user progress.")
                return json.load(f)
        else:
            print("No user progress file found. Initializing from item list.")
            # To avoid relative path issues, construct path relative to this file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(base_dir, '..', self.items_file), 'r') as f:
                return json.load(f)

    def save_progress(self):
        """Saves the current progress to a file."""
        # To avoid relative path issues, construct path relative to this file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base_dir, '..', self.data_file), 'w') as f:
            json.dump(self.progress, f, indent=4)
        print(f"Progress saved to {self.data_file}")

    def update_item_level(self, item_type, item_id, new_level):
        """Updates the level of a specific item."""
        items = self.progress.get(item_type, [])
        for item in items:
            if item.get('id') == item_id:
                item['current_uptie'] = new_level
                print(f"Updated {item_type} '{item_id}' to uptie {new_level}")
                self.save_progress()
                return True
        print(f"Warning: Item '{item_id}' not found in {item_type}.")
        return False

    def get_progress_visualization(self):
        """Generates a simple text-based visualization of progress."""
        # This will be replaced by data passed to the UI
        visualization = {}
        for item_type, items in self.progress.items():
            total_items = len(items)
            maxed_items = sum(1 for item in items if item['current_uptie'] == item['max_uptie'])
            visualization[item_type] = {
                "total": total_items,
                "maxed": maxed_items,
                "percentage": (maxed_items / total_items) * 100 if total_items > 0 else 0
            }
        return visualization
