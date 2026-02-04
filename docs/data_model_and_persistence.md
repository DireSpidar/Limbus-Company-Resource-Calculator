# Data Model & Persistence Design
## Limbus Company Resource Calculator

This document outlines a proposed data model and persistence strategy for
tracking user progress while supporting both manual and automated updates.

---

## Design Goals

- Separate static game data from user progress
- Support automation without risking data loss
- Enable safe updates when new content is added
- Keep storage human-readable and debuggable

---

## Data Separation

### Static Game Data
Stored separately and updated via GitHub.

Examples:
- Sinners
- E.G.O. definitions
- ID definitions
- Max levels and metadata

Example directory layout (conceptual):
```text
data/
  sinners.json
  egos.json
  ids.json
```

---

### User Progress Data
Frequently updated and never overwritten by static updates.

Example user data layout (conceptual):
```text
user_data/
  user_progress.json
```

---

## Conceptual User Progress Schema (Not Final)

```json
{
  "schema_version": 1,
  "sinners": {
    "Yi Sang": {
      "egos": {
        "Crow's Eye View": {
          "threadspin_level": 3
        }
      },
      "ids": {
        "LCB Sinner": {
          "uptie_level": 2,
          "experience_level": 30
        }
      }
    }
  }
}
```
