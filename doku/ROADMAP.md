# BearingNest roadmap

Versions are planned milestones, not implemented features or promised dates.

| Version | Scope | Completion criteria |
|---|---|---|
| 0.1.0 | Foundation | Implemented: owner template integration, version/lifecycle setup, three English tabs, integrated visual assets and environment documentation. Local checks pass; live Fusion acceptance checks remain open. |
| 0.2.0 | Geometry and edit proof | In progress: contour A confirmed; single-seat creation in 0.1.2 confirmed by the owner, with surface artifacts reported. Version 0.1.3 adds multi-position batches, direct cuts and profile-display changes, with live checks pending. Shaft modes, inner-ring relief, chamfer and persistent reopening/editing remain open. |
| 0.3.0 | Catalog and profiles | Verified seed bearings; custom records and source fields; named print profiles; auto/manual overrides and persistence. |
| 0.4.0 | Multiple seats and preview | Multi-selection and batch breakout/overlap checks implemented early in 0.1.3; live atomicity checks, red invalid seats and wall warnings remain open. |
| 0.5.0 | Robust editing | Lost-reference handling; stable updates; schema migration; component transforms and edge cases verified. |
| 0.6.0 | Printed trials | Compare 3/5/7/9 lands, width modes and correction presets; calibrate print defaults and document results. |
| 0.9.0 | Localization and release candidate | Introduce English source locale plus German translation; terminology review; install/uninstall and Fusion resource QA; complete guidance. |
| 1.0.0 | First stable release | Required checks and manual Fusion trials pass; library sources reviewed; license/publisher/repository links decided; owner publishes. |

## Immediate next steps

1. Complete the [0.1.0 live Fusion acceptance checks](INSTALLATION.md) on Windows and macOS and record Fusion builds.
2. [Contour A](CONTOUR_PROPOSAL.md) is confirmed by the owner, including derived transition width and axial extent. Use it for the single-seat prototype.
3. Run the 0.1.3 multiple-position and triangle regression checks, including invalid-batch rejection, preview cancel and undo/redo.
4. Add shaft modes, inner-ring relief and chamfer, then prove persistent reopening/editing before expanding to later milestones.
