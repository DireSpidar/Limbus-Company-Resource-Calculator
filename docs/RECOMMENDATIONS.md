# Recommendations for Rebuilding on `base-foundation-clean`
## Purpose
This document explains:
1) What is included in `base-foundation-clean` (the clean rebuild scaffold)
2) What changes to make when moving from the current `test-foundation` model to this structure
3) General improvements to reduce “messiness” during the rebuild

---

## What is included in `base-foundation-clean`

This branch is intentionally scaffolding-first: it provides structure + rules, not features.

### Directory overview (foundation)
- `docs/`
  - `FOUNDATION_NOTES.md` — guiding principles and rebuild rules
  - `RECOMMENDATIONS_FOR_JONAH.md` — this file

- `src/`
  - `README.md` — top-level layout explanation
  - `core/` — pure logic (no I/O, no UI)
  - `data/` — static schemas/content (safe to update)
  - `services/` — side effects (persistence, updates, OCR adapters)
    - `storage/` — load/save progress, backups, migrations
    - `updates/` — static data update mechanism + validation
  - `tracking/` — progress state + operations (no direct disk I/O)
  - `vision/` — recognition interfaces/adapters (returns events, does not mutate state)
  - `ui/` — UI layer (web/desktop) (calls tracking/core/services)
  - `app/` — application entrypoint(s) and dependency wiring
  - `utils/` — helpers

- `tests/`
  - placeholder for tests

This layout is meant to prevent UI, persistence, and business logic from becoming tangled.

---

## Why the current `test-foundation` starts to feel messy (what to avoid)

Observed patterns from `test-foundation`:
- UI (Flask routes) directly constructs `ProgressTracker` with file paths
- `ProgressTracker` mixes:
  - disk I/O (load/save)
  - state mutation (update_item_level)
  - progress reporting (visualization)
- sys.path modification in UI entrypoint to make imports work
- path handling split across multiple places


---

## Migration / Refactor Plan (recommended steps)

### Step 1 — Remove sys.path hacks by relying on package imports
Target outcome:
- No `sys.path.append(...)` inside UI entrypoints
- Use package imports like `from src.tracking...`

This requires:
- `src/__init__.py` and subpackage `__init__.py` files (already added in `base-foundation-clean`)

---

### Step 2 — Split persistence out of the tracker
Current pattern:
- `ProgressTracker.load_progress()` reads from disk
- `ProgressTracker.save_progress()` writes to disk

Recommended pattern:
- `services/storage` owns disk I/O:
  - `load_progress() -> dict/model`
  - `save_progress(progress) -> None`
- `tracking` owns state and operations:
  - `update_item_level(...)`
  - `get_progress_visualization()` (or move reporting to core if it becomes complex)

This makes it easier to test, easier to swap storage later, and reduces UI coupling.

---

### Step 3 — Make the UI depend on tracking/services, not file paths
Current:
- UI passes `'data/user_progress.json'` and `'data/items.json'` into ProgressTracker

Recommended:
- UI constructs services and passes them into tracking (dependency injection)
Example conceptually:
- storage = StorageService(progress_path=..., backup=...)
- tracker = ProgressTracker(storage=storage, static_data=loaded_items)
- UI uses tracker methods and receives data structures to render

Outcome:
- UI no longer knows where files live
- File structure can change without UI rewrites

---

### Step 4 — Enforce the “one entrypoint” rule
Avoid multiple competing entrypoints (e.g., both `src/main.py` and `src/app/main.py` starting the app).

Recommended:
- `src/app/main.py` is the only “start the app” file
- other modules are imported, not executed directly

This reduces confusion and accidental duplication.

---

### Step 5 — Keep static data updates separate from user progress
Goal:
- Updating `items.json` or other static content should never overwrite user progress.

Recommended:
- `src/data/` contains static schemas/definitions
- `src/services/updates/` handles updates + validation
- `src/services/storage/` handles user progress persistence only

---

## Where existing modules should land (mapping)

From `test-foundation`:
- `src/app/main.py`  -> `src/ui/` (UI code) + `src/app/main.py` (entrypoint wiring)
- `src/tracking/progress.py` -> split into:
  - `src/tracking/` (state + update operations)
  - `src/services/storage/` (load/save)
  - optional: `src/core/` (calculation/reporting logic as it grows)
- `src/vision/recognizer.py` -> `src/vision/` or `src/services/` depending on design:
  - If it’s a “pure recognizer interface”: `src/vision/`
  - If it does system I/O (screenshots): `src/services/` with a thin wrapper in `src/vision/`

---

## Minimal “clean rebuild” checklist
- [ ] No sys.path modification in app startup
- [ ] UI contains no disk I/O and minimal logic
- [ ] Tracking contains no disk I/O
- [ ] Storage is the only place that reads/writes progress
- [ ] Updates service is the only place that changes static data
- [ ] One clear entrypoint file


