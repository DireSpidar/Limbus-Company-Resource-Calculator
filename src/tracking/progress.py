import json
import os
import tempfile
import shutil

class ProgressTracker:
    def __init__(self, data_file='data/user_progress.json', items_file='data/items.json', ego_costs_file='data/ego_costs.json', sinners_file='data/sinners.json'):
        # Security: Use absolute paths resolved at initialization to prevent path traversal
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_file = os.path.join(self.base_dir, data_file)
        self.items_file = os.path.join(self.base_dir, items_file)
        self.ego_costs_file = os.path.join(self.base_dir, ego_costs_file)
        self.sinners_file = os.path.join(self.base_dir, sinners_file)
        
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        self.ego_costs = self._load_json_file(self.ego_costs_file, "E.G.O. costs")
        self.sinners = self._load_json_file(self.sinners_file, "Sinners")
        self.items_data = self._load_json_file(self.items_file, "Items")
        
        self._initialize_progress_if_needed()
        self.progress = self.load_progress()

    def _load_json_file(self, file_path, description):
        """Securely loads a JSON file."""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading {description} from {file_path}: {e}")
                return {}
        else:
            print(f"Warning: {description} file not found at {file_path}.")
            return {}

    def _initialize_progress_if_needed(self):
        """Initializes user progress if it doesn't exist."""
        if not os.path.exists(self.data_file):
            print("No user progress file found. Initializing from sinners and items list.")
            initial_progress = {
                "E.G.O.": [],
                "identities": []
            }

            # Initialize E.G.O.s from sinners.json
            for sinner_data in self.sinners.get('sinners', []):
                sinner_name = sinner_data.get('name', 'Unknown')
                for ego in sinner_data.get('egos', []):
                    initial_progress["E.G.O."].append({
                        "id": ego.get('id'),
                        "name": ego.get('name'),
                        "sinner": sinner_name,
                        "current_uptie": 0,
                        "max_uptie": 4,
                        "grade": ego.get('grade', "Zayin")
                    })
            
            # Load identities from items_data
            if 'identities' in self.items_data:
                initial_progress['identities'] = self.items_data['identities']

            self.progress = initial_progress
            self.save_progress()

    def load_progress(self):
        """Loads user progress securely."""
        return self._load_json_file(self.data_file, "User progress")

    def save_progress(self):
        """Saves the current progress atomically to prevent corruption."""
        try:
            # Create a temporary file in the same directory as the data file
            fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(self.data_file), prefix='progress_', suffix='.tmp')
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, indent=4)
            
            # Atomic swap
            os.replace(temp_path, self.data_file)
            print(f"Progress saved to {self.data_file}")
        except Exception as e:
            print(f"Error saving progress: {e}")
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)

    def reload_current_progress(self):
        """Reloads the current progress from the user progress file."""
        self.progress = self.load_progress()
        if not self.progress:
            self._initialize_progress_if_needed()
            self.progress = self.load_progress()

    EGO_GRADE_ORDER = {
        "Zayin": 0,
        "Teth": 1,
        "He": 2,
        "Waw": 3,
        "Aleph": 4
    }

    def _sort_egos_by_grade(self, egos):
        """Sorts a list of EGOs based on a predefined grade order."""
        def get_grade_sort_key(ego):
            return self.EGO_GRADE_ORDER.get(ego.get('grade'), 99)
        return sorted(egos, key=get_grade_sort_key)

    def _get_cost_for_level_range(self, grade, start_level, end_level):
        """Calculates the total thread and shards needed for an upgrade range."""
        total_thread = 0
        total_shards = 0

        if grade not in self.ego_costs:
            return 0, 0

        for level_transition in range(start_level, end_level):
            transition_key = f"{level_transition}->{level_transition + 1}"
            cost_data = self.ego_costs[grade].get(transition_key)
            if cost_data:
                total_thread += cost_data.get('thread', 0)
                total_shards += cost_data.get('shards', 0)

        return total_thread, total_shards

    def update_item_level(self, item_type, item_id, new_level):
        """Updates the level of a specific item with validation."""
        # Security: Validate inputs
        if item_type not in ["E.G.O.", "identities"]:
            print(f"Security Warning: Invalid item type '{item_type}'")
            return False
            
        try:
            new_level = int(new_level)
        except (ValueError, TypeError):
            print(f"Security Warning: Invalid level type '{type(new_level)}'")
            return False

        if not (0 <= new_level <= 4): # Standard game limit
            print(f"Security Warning: Level {new_level} out of bounds.")
            return False

        items = self.progress.get(item_type, [])
        for item in items:
            if item.get('id') == item_id:
                item['current_uptie'] = new_level
                print(f"Updated {item_type} '{item_id}' to level {new_level}")
                self.save_progress()
                return True
        print(f"Warning: Item '{item_id}' not found in {item_type}.")
        return False

    def get_sinner_progress(self):
        """Generates detailed progress data for the UI."""
        sinner_progress_list = []
        total_egos = 0
        total_maxed_egos = 0
        total_shards_spent = 0
        total_threads_spent = 0
        total_shards_max_all = 0
        total_threads_max_all = 0

        ego_progress_map = {item.get('id'): item for item in self.progress.get('E.G.O.', []) if item.get('id')}

        for sinner_data in self.sinners.get('sinners', []):
            sinner_name = sinner_data.get('name', 'Unknown')
            sinner_egos_static = sinner_data.get('egos', [])

            sinner_maxed_count = 0
            sinner_details_egos = []
            sinner_shards_spent = 0
            sinner_threads_spent = 0
            sinner_shards_max = 0
            sinner_threads_max = 0

            for ego_static in sinner_egos_static:
                ego_id = ego_static.get('id')
                ego_progress = ego_progress_map.get(ego_id)

                if ego_progress:
                    current_uptie = ego_progress.get('current_uptie', 0)
                    max_uptie = ego_progress.get('max_uptie', 4)
                    grade = ego_progress.get('grade', "Zayin")

                    s_thread, s_shards = self._get_cost_for_level_range(grade, 0, current_uptie)
                    m_thread, m_shards = self._get_cost_for_level_range(grade, 0, max_uptie)

                    sinner_shards_spent += s_shards
                    sinner_threads_spent += s_thread
                    sinner_shards_max += m_shards
                    sinner_threads_max += m_thread

                    sinner_details_egos.append({
                        "id": ego_id,
                        "name": ego_static.get('name', 'Unknown'),
                        "current_uptie": current_uptie,
                        "max_uptie": max_uptie,
                        "grade": grade
                    })

                    if current_uptie == max_uptie:
                        sinner_maxed_count += 1
            
            sinner_details_egos = self._sort_egos_by_grade(sinner_details_egos)
            num_egos = len(sinner_egos_static)
            total_egos += num_egos
            total_maxed_egos += sinner_maxed_count
            
            total_shards_spent += sinner_shards_spent
            total_threads_spent += sinner_threads_spent
            total_shards_max_all += sinner_shards_max
            total_threads_max_all += sinner_threads_max

            sinner_progress_list.append({
                "name": sinner_name,
                "maxed_egos_count": sinner_maxed_count,
                "total_egos_count": num_egos,
                "percentage_maxed_egos": (sinner_maxed_count / num_egos * 100) if num_egos > 0 else 0,
                "egos": sinner_details_egos,
                "resource_progress": {
                    "spent_shards": sinner_shards_spent,
                    "spent_threads": sinner_threads_spent,
                    "total_shards_possible": sinner_shards_max,
                    "total_threads_possible": sinner_threads_max,
                    "percentage": ((sinner_shards_spent + sinner_threads_spent) / (sinner_shards_max + sinner_threads_max) * 100) if (sinner_shards_max + sinner_threads_max) > 0 else 0
                }
            })

        total_possible_res = total_shards_max_all + total_threads_max_all
        total_spent_res = total_shards_spent + total_threads_spent
        
        return {
            "sinner_progress": sinner_progress_list,
            "total_maxed_egos_progress": {
                "maxed": total_maxed_egos,
                "total": total_egos,
                "percentage": (total_maxed_egos / total_egos * 100) if total_egos > 0 else 0
            },
            "total_resource_progress": {
                "spent_shards": total_shards_spent,
                "spent_threads": total_threads_spent,
                "total_shards_possible": total_shards_max_all,
                "total_threads_possible": total_threads_max_all,
                "percentage": (total_spent_res / total_possible_res * 100) if total_possible_res > 0 else 0
            }
        }
