# Changelog

## 0.1.1 - 2026-11-03

- Display the current release version after the BearingNest command name; synchronize the manifest and README.
- Record owner confirmation of the Solid > Create location and complete contour A proposal.
- Add a prototype snapshot codec with schema versioning, isolated bearing/profile data and stable identities across parameter revisions.
- Add a Fusion attribute adapter for storing/updating one record per feature, discovery and missing/ambiguous reference reporting.
- Keep storage separate from the UI until geometry creation and editing are proven in Fusion; it does not yet create or reopen seats.

Validation: 15 automated tests pass. Menu-label changes and persistence have not been live-tested in Fusion.

## 0.1.0 — 2026-11-03

- Moved the command to Solid > Create, added legacy toolbar cleanup and unified toolbar artwork in a dedicated resource folder. Live verification of these changes is pending.
- Prepared a dimensioned, mathematically tangent contour proposal for review before the 0.2.0 geometry implementation.
- Centralized the current version in `version.py`; plugin displays import it, and `tools/sync_version.py` synchronizes the manifest and README version header.
- Adapted the owner's Python add-in template for the BearingNest foundation.
- Registered one BearingNest command; disabled registration of sample palettes.
- Added Bearing Seat, Settings and About tabs with centralized English strings.
- Integrated project artwork into the add-in icon, command resources and About tab.
- Added manifest version 0.1.0 and included the previously ignored manifest and template utilities in the source package.
- Added repeatable command registration, toolbar cleanup and handler cleanup.
- Documented installation, target environments, API references and outstanding live checks.

Validation: Python syntax, manifest/version consistency, packaged resources and isolated lifecycle tests are checked locally. Live Fusion testing is pending. This version does not implement geometry, preview, persistent editing, a catalog or stored print profiles.
