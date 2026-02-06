import json
import os

class ProgressTracker:
    def __init__(self, data_file='data/user_progress.json', items_file='data/items.json', ego_costs_file='data/ego_costs.json', sinners_file='data/sinners.json'):
        self.data_file = data_file
        self.items_file = items_file
        self.ego_costs_file = ego_costs_file
        self.sinners_file = sinners_file
        self.ego_costs = self._load_ego_costs()
        self.sinners = self._load_sinners()
        self.items_data = self._load_items_data() # Load items data for identities
        self._initialize_progress_if_needed()
        self.progress = self.load_progress() # Load the actual progress after initialization

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

    def _load_items_data(self):
        """Loads item data (for identities) from items.json."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        items_path = os.path.join(base_dir, '..', self.items_file)
        if os.path.exists(items_path):
            with open(items_path, 'r') as f:
                return json.load(f)
        else:
            print(f"Warning: Items file not found at {items_path}. Identity information will not be available.")
            return {}

    def _initialize_progress_if_needed(self):
        """
        Initializes user progress if user_progress.json does not exist.
        It populates EGOs from sinners.json and identities from items.json.
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_file_path = os.path.join(base_dir, '..', self.data_file)

        if not os.path.exists(data_file_path):
            print("No user progress file found. Initializing from sinners and items list.")
            initial_progress = {
                "E.G.O.": [],
                "identities": []
            }

            # Initialize E.G.O.s from sinners.json
            for sinner_data in self.sinners.get('sinners', []):
                sinner_name = sinner_data['name']
                for ego in sinner_data['egos']:
                    # Grade is now directly in sinners.json
                    grade = ego.get('grade', "Zayin") # Get grade directly from sinners.json
                    max_uptie = 4 # Default max uptie for EGOs, consistent across current game EGOs

                    initial_progress["E.G.O."].append({
                        "id": ego['id'],
                        "name": ego['name'],
                        "sinner": sinner_name,
                        "current_uptie": 0,
                        "max_uptie": max_uptie,
                        "grade": grade
                    })
            
            # Load identities from items_data
            if 'identities' in self.items_data:
                initial_progress['identities'] = self.items_data['identities']

            self.progress = initial_progress
            self.save_progress() # Save the newly initialized progress
        # If the file exists, self.progress will be loaded by load_progress later

    def load_progress(self):
        """Loads user progress from a file, or initializes it if not found."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_file_path = os.path.join(base_dir, '..', self.data_file)

        if os.path.exists(data_file_path):
            with open(data_file_path, 'r') as f:
                print("Loading existing user progress.")
                return json.load(f)
        else:
            print("User progress file not found. _initialize_progress_if_needed has handled initialization.")
            return self.progress # Return the progress that was just initialized

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
            print(f"Warning: User progress file not found at {data_file_path}. Cannot reload progress. Re-initializing.")
            self._initialize_progress_if_needed() # Re-initialize if file somehow disappeared
            self.progress = self.load_progress() # Load the newly initialized progress

    def reload_items(self):
        """Reloads the items from the items_file and reinitializes progress."""
        # This method's intent seems to be to reset progress based on items.json
        # Given the new initialization logic, this might need re-evaluation.
        # For now, let's re-initialize everything.
        print(f"Items reloaded from {self.items_file}. Re-initializing full progress.")
        self._initialize_progress_if_needed() # This will effectively reset if items_file changes, as it rebuilds
        self.progress = self.load_progress() # Load the newly initialized progress

    # Define the custom order for E.G.O. grades
    EGO_GRADE_ORDER = {
        "Zayin": 0,
        "Teth": 1,
        "He": 2,
        "Waw": 3,
        "Aleph": 4 # Assuming Aleph is the highest grade for sorting purposes
    }

    def _sort_egos_by_grade(self, egos):
        """Sorts a list of EGOs based on a predefined grade order."""
        def get_grade_sort_key(ego):
            return self.EGO_GRADE_ORDER.get(ego.get('grade'), 99) # Default to high number for unknown grades
        
        return sorted(egos, key=get_grade_sort_key)


    def _get_cost_for_level_range(self, grade, start_level, end_level):
        """
        Calculates the total thread and shards needed to upgrade an E.G.O.
        from start_level to end_level for a given grade.
        """
        total_thread = 0
        total_shards = 0

        if grade not in self.ego_costs:
            return 0, 0 # Return 0 costs if grade data is missing

        for level_transition in range(start_level, end_level):
            transition_key = f"{level_transition}->{level_transition + 1}"
            cost_data = self.ego_costs[grade].get(transition_key)

            if not cost_data:
                continue

            total_thread += cost_data.get('thread', 0)
            total_shards += cost_data.get('shards', 0)

        return total_thread, total_shards


    def calculate_ego_upgrade_cost(self, item_id, target_level):
        """
        Calculates the total thread and shards needed to upgrade a specific E.G.O. to a target level.
        Assumes 'E.G.O.' item type for this calculation.
        """
        # Find the E.G.O. item to get its current level and grade
        ego_item = None
        # Ensure we are looking in the "E.G.O." key of self.progress
        for item in self.progress.get('E.G.O.', []):
            if item.get('id') == item_id:
                ego_item = item
                break

        if not ego_item:
            print(f"Error: E.G.O. item '{item_id}' not found in user progress.")
            return None, None

        current_level = ego_item.get('current_uptie', 0) # Use 'current_uptie' for E.G.O. level
        grade = ego_item.get('grade')

        if not grade:
            print(f"Error: E.G.O. item '{item_id}' has no grade defined.")
            return None, None

        # Use the new helper method
        return self._get_cost_for_level_range(grade, current_level, target_level)

    def update_item_level(self, item_type, item_id, new_level):
        """Updates the level of a specific item."""
        # Ensure new_level is within valid bounds (0 to max_uptie)
        if not (0 <= new_level <= 4): # Assuming max_uptie is generally 4 for EGOs
            print(f"Error: New level {new_level} for {item_type} '{item_id}' is out of valid range (0-4).")
            return False

        items = self.progress.get(item_type, [])
        for item in items:
            if item.get('id') == item_id:
                item['current_uptie'] = new_level
                print(f"Updated {item_type} '{item_id}' to uptie {new_level}")
                self.save_progress()
                return True
        print(f"Warning: Item '{item_id}' not found in {item_type}.")
        return False

    def get_sinner_progress(self):
        """
        Generates a detailed visualization of progress for each sinner,
        total maxed EGOs, and total resource progress.
        """
        sinner_progress_list = []
        total_egos = 0
        total_maxed_egos = 0

        total_shards_spent = 0
        total_threads_spent = 0
        total_shards_max_all = 0
        total_threads_max_all = 0

        # Map EGOs by their ID from the user's progress for quick lookup
        ego_progress_map = {item['id']: item for item in self.progress.get('E.G.O.', [])}

        for sinner_data in self.sinners.get('sinners', []):
            sinner_name = sinner_data['name']
            sinner_egos_from_static_data = sinner_data['egos'] # These are {id, name} objects

            sinner_maxed_count = 0
            sinner_details_egos = [] # To store individual EGO progress for this sinner

            # Per-sinner resource aggregation
            sinner_total_shards_spent = 0
            sinner_total_threads_spent = 0
            sinner_total_shards_max_all = 0
            sinner_total_threads_max_all = 0

            for ego_static_data in sinner_egos_from_static_data:
                ego_id = ego_static_data['id']
                ego_item_in_progress = ego_progress_map.get(ego_id)

                if ego_item_in_progress:
                    current_uptie = ego_item_in_progress.get('current_uptie', 0)
                    max_uptie = ego_item_in_progress.get('max_uptie', 4)
                    grade = ego_item_in_progress.get('grade', "Zayin") # Default grade if missing

                    # Calculate cost spent
                    spent_thread, spent_shards = self._get_cost_for_level_range(grade, 0, current_uptie)
                    # Aggregate for total app-wide resource progress
                    total_shards_spent += spent_shards
                    total_threads_spent += spent_thread
                    # Aggregate for per-sinner resource progress
                    sinner_total_shards_spent += spent_shards
                    sinner_total_threads_spent += spent_thread


                    # Calculate total possible cost for this EGO
                    max_thread, max_shards = self._get_cost_for_level_range(grade, 0, max_uptie)
                    # Aggregate for total app-wide resource progress
                    total_shards_max_all += max_shards
                    total_threads_max_all += max_thread
                    # Aggregate for per-sinner resource progress
                    sinner_total_shards_max_all += max_shards
                    sinner_total_threads_max_all += max_thread

                    sinner_details_egos.append({
                        "id": ego_id,
                        "name": ego_static_data['name'],
                        "current_uptie": current_uptie,
                        "max_uptie": max_uptie,
                        "grade": grade,
                        "spent_thread": spent_thread,
                        "spent_shards": spent_shards,
                        "total_max_thread": max_thread,
                        "total_max_shards": max_shards
                    })

                    if current_uptie == max_uptie:
                        sinner_maxed_count += 1
            
            # Sort individual EGOs by grade
            sinner_details_egos = self._sort_egos_by_grade(sinner_details_egos)

            total_sinner_egos = len(sinner_egos_from_static_data)
            total_egos += total_sinner_egos
            total_maxed_egos += sinner_maxed_count
            
            percentage_maxed_egos = (sinner_maxed_count / total_sinner_egos) * 100 if total_sinner_egos > 0 else 0

            # Calculate per-sinner combined resource progress
            sinner_total_possible_resource_units = sinner_total_shards_max_all + sinner_total_threads_max_all
            sinner_total_spent_resource_units = sinner_total_shards_spent + sinner_total_threads_spent
            sinner_resource_percentage = (sinner_total_spent_resource_units / sinner_total_possible_resource_units) * 100 if sinner_total_possible_resource_units > 0 else 0
            
            sinner_progress_list.append({
                "name": sinner_name,
                "maxed_egos_count": sinner_maxed_count,
                "total_egos_count": total_sinner_egos,
                "percentage_maxed_egos": percentage_maxed_egos,
                "egos": sinner_details_egos,
                "resource_progress": { # New per-sinner resource progress
                    "spent_shards": sinner_total_shards_spent,
                    "spent_threads": sinner_total_threads_spent,
                    "total_shards_possible": sinner_total_shards_max_all,
                    "total_threads_possible": sinner_total_threads_max_all,
                    "percentage": sinner_resource_percentage
                }
            })

        # Calculate combined resource progress for total app-wide
        total_possible_resource_units = total_shards_max_all + total_threads_max_all
        total_spent_resource_units = total_shards_spent + total_threads_spent
        
        resource_progress_percentage = (total_spent_resource_units / total_possible_resource_units) * 100 if total_possible_resource_units > 0 else 0

        total_percentage_maxed_egos = (total_maxed_egos / total_egos) * 100 if total_egos > 0 else 0
        
        return {
            "sinner_progress": sinner_progress_list,
            "total_maxed_egos_progress": {
                "maxed": total_maxed_egos,
                "total": total_egos,
                "percentage": total_percentage_maxed_egos
            },
            "total_resource_progress": {
                "spent_shards": total_shards_spent,
                "spent_threads": total_threads_spent,
                "total_shards_possible": total_shards_max_all,
                "total_threads_possible": total_threads_max_all,
                "percentage": resource_progress_percentage
            }
        }