import json
import os
import sys

class ProgressTracker:
    def __init__(self, data_file='data/user_progress.json', items_file='data/items.json', ego_costs_file='data/ego_costs.json', sinners_file='data/sinners.json'):
        # Determine the base path for persistent data
        if getattr(sys, 'frozen', False):
            # If running as a bundled EXE, base_dir is the directory of the EXE
            self.base_dir = os.path.dirname(sys.executable)
            self.read_only_base = sys._MEIPASS
        else:
            # If running from source, base_dir is the project root
            self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            self.read_only_base = self.base_dir

        self.data_file = data_file
        self.items_file = items_file
        self.ego_costs_file = ego_costs_file
        self.sinners_file = sinners_file
        
        # Path for persistent user progress
        self.data_path = os.path.join(self.base_dir, self.data_file)

        self.ego_costs = self._load_ego_costs()
        self.sinners = self._load_sinners()
        self.items_data = self._load_items_data() 
        self._initialize_progress_if_needed()
        self.progress = self.load_progress() 
        self.ocr_enabled = False 

    def _load_sinners(self):
        """Loads sinner data from a file."""
        path = os.path.join(self.read_only_base, 'src', self.sinners_file)
        if not os.path.exists(path):
            path = os.path.join(self.base_dir, self.sinners_file)
        
        if os.path.exists(path):
            with open(path, 'r', encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _load_items_data(self):
        """Loads item data (for identities) from items.json."""
        path = os.path.join(self.read_only_base, 'src', self.items_file)
        if not os.path.exists(path):
            path = os.path.join(self.base_dir, self.items_file)
            
        if os.path.exists(path):
            with open(path, 'r', encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _initialize_progress_if_needed(self):
        """Initializes user progress if user_progress.json does not exist."""
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)

        if not os.path.exists(self.data_path):
            print(f"Initializing new progress file at {self.data_path}")
            initial_progress = {"E.G.O.": [], "identities": []}
            for sinner_data in self.sinners.get('sinners', []):
                sinner_name = sinner_data['name']
                for ego in sinner_data['egos']:
                    initial_progress["E.G.O."].append({
                        "id": ego['id'],
                        "name": ego['name'],
                        "sinner": sinner_name,
                        "current_uptie": 0,
                        "max_uptie": 4,
                        "grade": ego.get('grade', "Zayin")
                    })
            if 'identities' in self.items_data:
                initial_progress['identities'] = self.items_data['identities']
            self.progress = initial_progress
            self.save_progress()

    def load_progress(self):
        """Loads user progress from a file."""
        if os.path.exists(self.data_path):
            with open(self.data_path, 'r', encoding="utf-8") as f:
                return json.load(f)
        return self.progress

    def _load_ego_costs(self):
        """Loads E.G.O. upgrade costs from a file."""
        path = os.path.join(self.read_only_base, 'src', self.ego_costs_file)
        if not os.path.exists(path):
            path = os.path.join(self.base_dir, self.ego_costs_file)
        if os.path.exists(path):
            with open(path, 'r', encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_progress(self):
        """Saves the current progress to a file."""
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        with open(self.data_path, 'w', encoding="utf-8") as f:
            json.dump(self.progress, f, indent=4)

    def reload_current_progress(self):
        """Reloads the current progress from the user progress file."""
        if os.path.exists(self.data_path):
            with open(self.data_path, 'r', encoding="utf-8") as f:
                self.progress = json.load(f)
        else:
            self._initialize_progress_if_needed()
            self.progress = self.load_progress()

    def reset_all_progress(self):
        """Resets all items' current_uptie to 0 and saves."""
        print("Resetting all progress to 0...")
        for item_type in ["E.G.O.", "identities"]:
            if item_type in self.progress:
                for item in self.progress[item_type]:
                    item['current_uptie'] = 0
        self.save_progress()

    def update_item_level(self, item_type, item_id, new_level):
        """Updates the level of a specific item."""
        if not (0 <= new_level <= 4):
            return False
        items = self.progress.get(item_type, [])
        for item in items:
            if item.get('id') == item_id:
                item['current_uptie'] = new_level
                self.save_progress()
                return True
        return False

    EGO_GRADE_ORDER = {"Zayin": 0, "Teth": 1, "He": 2, "Waw": 3, "Aleph": 4}

    def _sort_egos_by_grade(self, egos):
        return sorted(egos, key=lambda x: self.EGO_GRADE_ORDER.get(x.get('grade'), 99))

    def _get_cost_for_level_range(self, grade, start_level, end_level):
        total_thread, total_shards = 0, 0
        if grade not in self.ego_costs:
            return 0, 0
        for level_transition in range(start_level, end_level):
            transition_key = f"{level_transition}->{level_transition + 1}"
            cost_data = self.ego_costs[grade].get(transition_key)
            if cost_data:
                total_thread += cost_data.get('thread', 0)
                total_shards += cost_data.get('shards', 0)
        return total_thread, total_shards

    def get_sinner_progress(self):
        sinner_progress_list = []
        total_egos, total_maxed_egos = 0, 0
        total_shards_spent, total_threads_spent = 0, 0
        total_shards_max_all, total_threads_max_all = 0, 0

        ego_progress_map = {item['id']: item for item in self.progress.get('E.G.O.', [])}

        for sinner_data in self.sinners.get('sinners', []):
            sinner_name = sinner_data['name']
            sinner_egos_from_static_data = sinner_data['egos']
            sinner_maxed_count = 0
            sinner_details_egos = []
            s_shards_spent, s_threads_spent = 0, 0
            s_shards_max, s_threads_max = 0, 0

            for ego_static_data in sinner_egos_from_static_data:
                ego_id = ego_static_data['id']
                ego_item = ego_progress_map.get(ego_id)
                if ego_item:
                    curr, mx, grd = ego_item.get('current_uptie', 0), ego_item.get('max_uptie', 4), ego_item.get('grade', "Zayin")
                    sp_t, sp_s = self._get_cost_for_level_range(grd, 0, curr)
                    mx_t, mx_s = self._get_cost_for_level_range(grd, 0, mx)
                    
                    total_shards_spent += sp_s
                    total_threads_spent += sp_t
                    total_shards_max_all += mx_s
                    total_threads_max_all += mx_t
                    
                    s_shards_spent += sp_s
                    s_threads_spent += sp_t
                    s_shards_max += mx_s
                    s_threads_max += mx_t

                    sinner_details_egos.append({
                        "id": ego_id, "name": ego_static_data['name'], "current_uptie": curr, "max_uptie": mx, "grade": grd,
                        "spent_thread": sp_t, "spent_shards": sp_s, "total_max_thread": mx_t, "total_max_shards": mx_s
                    })
                    if curr == mx: sinner_maxed_count += 1
            
            sinner_details_egos = self._sort_egos_by_grade(sinner_details_egos)
            total_sinner_egos = len(sinner_egos_from_static_data)
            total_egos += total_sinner_egos
            total_maxed_egos += sinner_maxed_count
            
            perc_maxed = (sinner_maxed_count / total_sinner_egos * 100) if total_sinner_egos > 0 else 0
            s_total_max = s_shards_max + s_threads_max
            s_total_spent = s_shards_spent + s_threads_spent
            s_res_perc = (s_total_spent / s_total_max * 100) if s_total_max > 0 else 0
            
            sinner_progress_list.append({
                "name": sinner_name, "maxed_egos_count": sinner_maxed_count, "total_egos_count": total_sinner_egos,
                "percentage_maxed_egos": perc_maxed, "egos": sinner_details_egos,
                "resource_progress": {
                    "spent_shards": s_shards_spent, "spent_threads": s_threads_spent,
                    "total_shards_possible": s_shards_max, "total_threads_possible": s_threads_max, "percentage": s_res_perc
                }
            })

        t_max = total_shards_max_all + total_threads_max_all
        t_spent = total_shards_spent + total_threads_spent
        res_perc = (t_spent / t_max * 100) if t_max > 0 else 0
        total_perc_maxed = (total_maxed_egos / total_egos * 100) if total_egos > 0 else 0
        
        return {
            "sinner_progress": sinner_progress_list,
            "total_maxed_egos_progress": {"maxed": total_maxed_egos, "total": total_egos, "percentage": total_perc_maxed},
            "total_resource_progress": {
                "spent_shards": total_shards_spent, "spent_threads": total_threads_spent,
                "total_shards_possible": total_shards_max_all, "total_threads_possible": total_threads_max_all, "percentage": res_perc
            }
        }
