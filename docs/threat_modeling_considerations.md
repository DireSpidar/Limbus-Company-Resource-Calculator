# Threat Modeling & Security Considerations
## Limbus Company Resource Calculator

This document provides an initial threat modeling and security review for the
Limbus Company Resource Calculator. The goal is to identify client-side risks
early and guide safer design decisions as the project evolves.

---

## Scope

- Client-side only application
- Single-player game context
- No interaction with official game servers
- Optional user-initiated updates from GitHub

Primary risks are local system and data integrity related rather than
network-based.

---

## Assets

- User progress data (uptie, threadspin, experience levels)
- Local configuration files
- Application integrity and expected behavior
- User trust in automated detection

---

## Threats & Mitigations

### Local Data Integrity
- Risk of corrupted or overwritten progress data
- OCR mis-detection causing incorrect updates

Mitigations:
- Manual confirmation for automated changes
- Versioned backups of progress files
- Atomic file writes

---

### Screen Monitoring & Overlay
- Overlay conflicts with Linux compositors
- Performance impact during continuous monitoring

Mitigations:
- User-controlled automation toggles
- Adjustable capture frequency
- Non-intrusive overlay design

---

### Update Mechanism
- Corrupted or incompatible data updates
- Schema changes breaking user data

Mitigations:
- Versioned data schemas
- Validation before applying updates
- Manual update initiation only

---

## Privacy Considerations

- No credentials or personal data collected
- No network activity unless explicitly triggered
- Screenshots processed in-memory only

---

## Assumptions

- No game memory modification
- No gameplay automation
- No DRM or anti-cheat bypassing
