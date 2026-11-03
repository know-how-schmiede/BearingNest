# Changelog

## 0.1.0 — 2026-11-03

- Centralized the current version in `version.py`; plugin displays import it, and `tools/sync_version.py` synchronizes the manifest and README version header.
- Adapted the owner's Python add-in template for the BearingNest foundation.
- Registered one BearingNest command; disabled registration of sample palettes.
- Added Bearing Seat, Settings and About tabs with centralized English strings.
- Integrated project artwork into the add-in icon, command resources and About tab.
- Added manifest version 0.1.0 and included the previously ignored manifest and template utilities in the source package.
- Added repeatable command registration, toolbar cleanup and handler cleanup.
- Documented installation, target environments, API references and outstanding live checks.

Validation: Python syntax, manifest/version consistency, packaged resources and isolated lifecycle tests are checked locally. Live Fusion testing is pending. This version does not implement geometry, preview, persistent editing, a catalog or stored print profiles.
