import json
import os

class ProgressTracker:
    def __init__(self, data_file='data/user_progress.json', items_file='data/items.json', ego_costs_file='data/ego_costs.json', sinners_file='data/sinners.json'):
        self.data_file = data_file
        self.items_file = items_file
        self.ego_costs_file = ego_costs_file
        self.sinners_file = sinners_file
        self.progress = self.load_progress()
        self.ego_costs = self._load_ego_costs()
        self.sinners = self._load_sinners()

    def _load_sinners(self):
        """Loads sinner data from a file."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        sinners_path = os.path.join(base_dir, '..', self.sinners_file)
        if os.path.exists(sinners_path):
            with open(sinners_path, 'r') as f:
                return json.load(f)
        else:
            print(f"Warning: Sinners file not found at {sinners_path}. Sinner information will not be available.")
            return {}

    def load_progress(self):
        """Loads user progress from a file, or initializes it from the base items file."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_file_path = os.path.join(base_dir, '..', self.data_file)

        if os.path.exists(data_file_path):
            with open(data_file_path, 'r') as f:
                print("Loading existing user progress.")
                return json.load(f)
        else:
            print("No user progress file found. Initializing from item list.")
            items_file_path = os.path.join(base_dir, '..', self.items_file)
            with open(items_file_path, 'r') as f:
                return json.load(f)

    def _load_ego_costs(self):
        """Loads E.G.O. upgrade costs from a file."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ego_costs_path = os.path.join(base_dir, '..', self.ego_costs_file)
        if os.path.exists(ego_costs_path):
            with open(ego_costs_path, 'r') as f:
                return json.load(f)
        else:
            print(f"Warning: E.G.O. costs file not found at {ego_costs_path}. E.G.O. cost calculations will not be available.")
            return {}

    def save_progress(self):
        """Saves the current progress to a file."""
        # To avoid relative path issues, construct path relative to this file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base_dir, '..', self.data_file), 'w') as f:
            json.dump(self.progress, f, indent=4)
        print(f"Progress saved to {self.data_file}")

    def reload_current_progress(self):
        """Reloads the current progress from the user progress file."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_file_path = os.path.join(base_dir, '..', self.data_file)
        if os.path.exists(data_file_path):
            with open(data_file_path, 'r') as f:
                self.progress = json.load(f)
            print("Current user progress reloaded.")
        else:
            print(f"Warning: User progress file not found at {data_file_path}. Cannot reload progress.")

    def reload_items(self):
        """Reloads the items from the items_file and reinitializes progress."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_items_file_path = os.path.join(base_dir, '..', self.items_file)
        with open(full_items_file_path, 'r') as f:
            self.progress = json.load(f)
        print(f"Items reloaded from {self.items_file}")

    def calculate_ego_upgrade_cost(self, item_id, target_level):
        """
        Calculates the total thread and shards needed to upgrade a specific E.G.O. to a target level.
        Assumes 'E.G.O.' item type for this calculation.
        """
        total_thread = 0
        total_shards = 0

        # Find the E.G.O. item to get its current level and grade
        ego_item = None
        for item in self.progress.get('E.G.O.', []):
            if item.get('id') == item_id:
                ego_item = item
                break

        if not ego_item:
            print(f"Error: E.G.O. item '{item_id}' not found.")
            return None, None

        current_level = ego_item.get('current_uptie', 0) # Use 'current_uptie' for E.G.O. level
        grade = ego_item.get('grade')

        if not grade:
            print(f"Error: E.G.O. item '{item_id}' has no grade defined.")
            return None, None

        if grade not in self.ego_costs:
            print(f"Error: No cost data found for E.G.O. grade '{grade}'.")
            return None, None

        for level_transition in range(current_level, target_level):
            transition_key = f"{level_transition}->{level_transition + 1}"
            cost_data = self.ego_costs[grade].get(transition_key)

            if not cost_data:
                print(f"Warning: No cost data for {grade} E.G.O. from level {level_transition} to {level_transition + 1}.")
                continue

            total_thread += cost_data.get('thread', 0)
            total_shards += cost_data.get('shards', 0)

        return total_thread, total_shards

    def update_item_level(self, item_type, item_id, new_level):
        """Updates the level of a specific item."""
        items = self.progress.get(item_type, [])
        for item in items:
            if item.get('id') == item_id:
                item['current_uptie'] = new_level
                print(f"Updated {item_type} '{item_id}' to uptie {new_level}")
                self.save_progress()
                self.reload_current_progress() # Reload progress after saving
                return True
        print(f"Warning: Item '{item_id}' not found in {item_type}.")
        return False

    def get_sinner_progress(self):
        """Generates a detailed visualization of progress for each sinner and total progress."""
        sinner_progress = []
        total_egos = 0
        total_maxed_egos = 0

        ego_progress_map = {item['name']: item for item in self.progress.get('E.G.O.', [])}

        for sinner in self.sinners.get('sinners', []):
            sinner_name = sinner['name']
            sinner_egos = sinner['egos']
            
            maxed_count = 0
            for ego_name in sinner_egos:
                ego_item = ego_progress_map.get(ego_name)
                if ego_item and ego_item.get('current_uptie') == ego_item.get('max_uptie'):
                    maxed_count += 1
            
            total_sinner_egos = len(sinner_egos)
            total_egos += total_sinner_egos
            total_maxed_egos += maxed_count
            
            percentage = (maxed_count / total_sinner_egos) * 100 if total_sinner_egos > 0 else 0
            
            sinner_progress.append({
                "name": sinner_name,
                "maxed": maxed_count,
                "total": total_sinner_egos,
                "percentage": percentage
            })

        total_percentage = (total_maxed_egos / total_egos) * 100 if total_egos > 0 else 0
        
        return {
            "sinner_progress": sinner_progress,
            "total_progress": {
                "maxed": total_maxed_egos,
                "total": total_egos,
                "percentage": total_percentage
            }
        }

