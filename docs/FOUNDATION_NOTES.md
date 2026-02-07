# Base Foundation Notes (Clean Restart)

Goal: Provide a clean base that supports:
- Manual tracking first
- Automated tracking later (screen capture/OCR)
- Safe updates for static data
- Clear separation of UI vs logic vs data

Principles:
- UI does not contain business logic
- Core logic performs no I/O
- Services handle I/O (disk/network/screen)
- Static data updates must not overwrite user progress
