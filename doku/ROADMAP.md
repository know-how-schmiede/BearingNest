# BearingNest roadmap

Versions are planned milestones, not implemented features or promised dates.

| Version | Scope | Completion criteria |
|---|---|---|
| 0.1.0 | Foundation | Implemented: owner template integration, version/lifecycle setup, three English tabs, integrated visual assets and environment documentation. Local checks pass; live Fusion acceptance checks remain open. |
| 0.2.0 | Geometry and edit proof | Confirm dimensioned rounded contour; one seat on one face; corrections, shaft modes and inner-ring relief; prove persistent reopening/editing. |
| 0.3.0 | Catalog and profiles | Verified seed bearings; custom records and source fields; named print profiles; auto/manual overrides and persistence. |
| 0.4.0 | Multiple seats and preview | Multi-selection; red invalid seats and reasons; wall warnings; breakout/overlap checks; safe commit/cancel. |
| 0.5.0 | Robust editing | Lost-reference handling; stable updates; schema migration; component transforms and edge cases verified. |
| 0.6.0 | Printed trials | Compare 3/5/7/9 lands, width modes and correction presets; calibrate print defaults and document results. |
| 0.9.0 | Localization and release candidate | Introduce English source locale plus German translation; terminology review; install/uninstall and Fusion resource QA; complete guidance. |
| 1.0.0 | First stable release | Required checks and manual Fusion trials pass; library sources reviewed; license/publisher/repository links decided; owner publishes. |

## Immediate next steps

1. Complete the [0.1.0 live Fusion acceptance checks](INSTALLATION.md) on Windows and macOS and record Fusion builds.
2. [Contour A](CONTOUR_PROPOSAL.md) is confirmed by the owner, including derived transition width and axial extent. Use it for the single-seat prototype.
3. Prototype supported Fusion geometry and editing for 0.2.0. Snapshot serialization and the attribute/reference adapter are implemented and covered by isolated tests; live file reopen and geometry edits remain unproven.
4. Implement one-seat geometry and persistent reopening/editing before expanding to later milestones.
