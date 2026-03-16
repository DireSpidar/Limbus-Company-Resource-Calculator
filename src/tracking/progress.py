import json
import sys
from pathlib import Path


def bundled_base_path() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[2]


def writable_base_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


class ProgressTracker:
    EGO_GRADE_ORDER = {"Zayin": 0, "Teth": 1, "He": 2, "Waw": 3, "Aleph": 4}

    def __init__(
        self,
        data_file="data/user_progress.json",
        items_file="src/data/items.json",
        ego_costs_file="src/data/ego_costs.json",
        sinners_file="src/data/sinners.json"
    ):
        self.read_only_base = bundled_base_path()
        self.base_dir = writable_base_path()

        self.data_file = Path(data_file)
        self.items_file = Path(items_file)
        self.ego_costs_file = Path(ego_costs_file)
        self.sinners_file = Path(sinners_file)

        self.data_path = self.base_dir / self.data_file

        self.ego_costs = self._load_json_file(self.ego_costs_file, default={})
        self.sinners = self._load_json_file(self.sinners_file, default={})
        self.items_data = self._load_json_file(self.items_file, default={})

        self._initialize_progress_if_needed()
        self.progress = self.load_progress()
        self.ocr_enabled = False

    def _resolve_readonly_path(self, relative_path: Path) -> Path:
        primary = self.read_only_base / relative_path
        if primary.exists():
            return primary
        return self.base_dir / relative_path

    def _load_json_file(self, relative_path: Path, default=None):
        if default is None:
            default = {}

        path = self._resolve_readonly_path(relative_path)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load JSON from {path}: {e}")

        return default

    def _initialize_progress_if_needed(self):
        self.data_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.data_path.exists():
            print(f"Initializing new progress file at {self.data_path}")

            initial_progress = {"E.G.O.": [], "identities": []}

            for sinner_data in self.sinners.get("sinners", []):
                sinner_name = sinner_data.get("name")
                for ego in sinner_data.get("egos", []):
                    initial_progress["E.G.O."].append({
                        "id": ego.get("id"),
                        "name": ego.get("name"),
                        "sinner": sinner_name,
                        "current_uptie": 0,
                        "max_uptie": 4,
                        "grade": ego.get("grade", "Zayin")
                    })

            if "identities" in self.items_data:
                initial_progress["identities"] = self.items_data["identities"]

            self.progress = initial_progress
            self.save_progress()

    def load_progress(self):
        if self.data_path.exists():
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load progress from {self.data_path}: {e}")

        return getattr(self, "progress", {"E.G.O.": [], "identities": []})

    def save_progress(self):
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self.progress, f, indent=4, ensure_ascii=False)

    def reload_current_progress(self):
        if self.data_path.exists():
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    self.progress = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to reload progress: {e}")
        else:
            self._initialize_progress_if_needed()
            self.progress = self.load_progress()

    def reload_items(self):
        self.items_data = self._load_json_file(self.items_file, default={})

    def _load_ego_costs(self):
        return self._load_json_file(self.ego_costs_file, default={})

    def _load_sinners(self):
        return self._load_json_file(self.sinners_file, default={})

    def _load_items_data(self):
        return self._load_json_file(self.items_file, default={})

    def reset_all_progress(self):
        print("Resetting all progress to 0...")
        for item_type in ["E.G.O.", "identities"]:
            if item_type in self.progress:
                for item in self.progress[item_type]:
                    item["current_uptie"] = 0
        self.save_progress()

    def update_item_level(self, item_type, item_id, new_level):
        if not (0 <= new_level <= 4):
            return False

        items = self.progress.get(item_type, [])
        for item in items:
            if item.get("id") == item_id:
                item["current_uptie"] = new_level
                self.save_progress()
                return True

        return False

    def _sort_egos_by_grade(self, egos):
        return sorted(egos, key=lambda x: self.EGO_GRADE_ORDER.get(x.get("grade"), 99))

    def _get_cost_for_level_range(self, grade, start_level, end_level):
        total_thread = 0
        total_shards = 0

        if grade not in self.ego_costs:
            return 0, 0

        for level_transition in range(start_level, end_level):
            transition_key = f"{level_transition}->{level_transition + 1}"
            cost_data = self.ego_costs[grade].get(transition_key)
            if cost_data:
                total_thread += cost_data.get("thread", 0)
                total_shards += cost_data.get("shards", 0)

        return total_thread, total_shards

    def calculate_ego_upgrade_cost(self, item_id, target_level):
        for item in self.progress.get("E.G.O.", []):
            if item.get("id") == item_id:
                current_level = item.get("current_uptie", 0)
                grade = item.get("grade", "Zayin")
                return self._get_cost_for_level_range(grade, current_level, target_level)

        return 0, 0

    def get_sinner_progress(self):
        return {
            "sinner_progress": [],
            "total_maxed_egos_progress": {"maxed": 0, "total": 0, "percentage": 0},
            "total_resource_progress": {
                "spent_shards": 0,
                "spent_threads": 0,
                "total_shards_possible": 0,
                "total_threads_possible": 0,
                "percentage": 0
            }
        }
            
        
