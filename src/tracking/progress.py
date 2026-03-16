import json
import sys
from pathlib import Path


def bundled_base_path() -> Path:
    """
    Read-only bundled files location.
    In PyInstaller builds this is the unpacked temp bundle.
    In development this is the project root.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[2]


def writable_base_path() -> Path:
    """
    Writable user-data location.
    In packaged builds, store next to the EXE.
    In development, store in the project root.
    """
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

        fallback = self.base_dir / relative_path
        return fallback

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

            initial_progress = {
                "E.G.O.": [],
                "identities": []
            }

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
        return sorted(
            egos,
            key=lambda x: self.EGO_GRADE_ORDER.get(x.get("grade"), 99)
        )

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
        sinner_progress_list = []
        total_egos = 0
        total_maxed_egos = 0
        total_shards_spent = 0
        total_threads_spent = 0
        total_shards_max_all = 0
        total_threads_max_all = 0

        ego_progress_map = {
            item["id"]: item for item in self.progress.get("E.G.O.", [])
            if item.get("id") is not None
        }

        for sinner_data in self.sinners.get("sinners", []):
            sinner_name = sinner_data.get("name")
            sinner_egos_from_static_data = sinner_data.get("egos", [])
            sinner_maxed_count = 0
            sinner_details_egos = []
            s_shards_spent = 0
            s_threads_spent = 0
            s_shards_max = 0
            s_threads_max = 0

            for ego_static_data in sinner_egos_from_static_data:
                ego_id = ego_static_data.get("id")
                ego_item = ego_progress_map.get(ego_id)

                if ego_item:
                    curr = ego_item.get("current_uptie", 0)
                    mx = ego_item.get("max_uptie", 4)
                    grd = ego_item.get("grade", "Zayin")

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
                        "id": ego_id,
                        "name": ego_static_data.get("name"),
                        "current_uptie": curr,
                        "max_uptie": mx,
                        "grade": grd,
                        "spent_thread": sp_t,
                        "spent_shards": sp_s,
                        "total_max_thread": mx_t,
                        "total_max_shards": mx_s
                    })

                    if curr == mx:
                        sinner_maxed_count += 1

            sinner_details_egos = self._sort_egos_by_grade(sinner_details_egos)
            total_sinner_egos = len(sinner_egos_from_static_data)
            total_egos += total_sinner_egos
            total_maxed_egos += sinner_maxed_count

            perc_maxed = (sinner_maxed_count / total_sinner_egos * 100) if total_sinner_egos > 0 else 0
            s_total_max = s_shards_max + s_threads_max
            s_total_spent = s_shards_spent + s_threads_spent
            s_res_perc = (s_total_spent / s_total_max * 100) if s_total_max > 0 else 0

            sinner_progress_list.append({
                "name": sinner_name,
                "maxed_egos_count": sinner_maxed_count,
                "total_egos_count": total_sinner_egos,
                "percentage_maxed_egos": perc_maxed,
                "egos": sinner_details_egos,
                "resource_progress": {
                    "spent_shards": s_shards_spent,
                    "spent_threads": s_threads_spent,
                    "total_shards_possible": s_shards_max,
                    "total_threads_possible": s_threads_max,
                    "percentage": s_res_perc
                }
            })

        t_max = total_shards_max_all + total_threads_max_all
        t_spent = total_shards_spent + total_threads_spent
        res_perc = (t_spent / t_max * 100) if t_max > 0 else 0
        total_perc_maxed = (total_maxed_egos / total_egos * 100) if total_egos > 0 else 0

        return {
            "sinner_progress": sinner_progress_list,
            "total_maxed_egos_progress": {
                "maxed": total_maxed_egos,
                "total": total_egos,
                "percentage": total_perc_maxed
            },
            "total_resource_progress": {
                "spent_shards": total_shards_spent,
                "spent_threads": total_threads_spent,
                "total_shards_possible": total_shards_max_all,
                "total_threads_possible": total_threads_max_all,
                "percentage": res_perc
            }
        }
