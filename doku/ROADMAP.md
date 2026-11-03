# BearingNest roadmap

Versions are planned milestones, not implemented features or promised dates.

| Version | Scope | Completion criteria |
|---|---|---|
| 0.1.0 | Foundation | Implemented: owner template integration, version/lifecycle setup, three English tabs, integrated assets and environment documentation. Owner reported no observed errors in the 0.1.8 trial on 2026-11-03; full platform/build acceptance remains open. |
| 0.2.0 | Geometry and edit proof | Prototype implementation available: contour A, shaft/inner-ring cuts, optional 45-degree chamfer and snapshot-driven whole-batch editing. Editing is limited to the last complete batch without downstream features/groups. Owner accepted the 0.1.8 baseline; new 0.2.0 geometry, save/reopen, editing, cancel and undo/redo still need live Fusion proof before closing this milestone. |
| 0.3.0 | Catalog and profiles | Verified seed bearings; custom records and source fields; named print profiles; auto/manual overrides and persistence. |
| 0.4.0 | Multiple seats and preview | Multi-selection and batch breakout/overlap checks implemented early in 0.1.3; live atomicity checks, red invalid seats and wall warnings remain open. |
| 0.5.0 | Robust editing | Lost-reference handling; stable updates; schema migration; component transforms and edge cases verified. |
| 0.6.0 | Printed trials | Compare 3/5/7/9 lands, width modes and correction presets; calibrate print defaults and document results. |
| 0.9.0 | Localization and release candidate | Introduce English source locale plus German translation; terminology review; install/uninstall and Fusion resource QA; complete guidance. |
| 1.0.0 | First stable release | Required checks and manual Fusion trials pass; library sources reviewed; license/publisher/repository links decided; owner publishes. |

## Immediate next steps

1. Run the [0.2.0 chamfer/edit acceptance procedure](INSTALLATION.md#020-chamfer-and-edit-acceptance) on a disposable design and record the Fusion build and OS.
2. Verify save/reopen discovery, stable seat IDs, repeated edits, failed updates, preview cancel and single-command undo/redo. Automated API-substitute checks do not complete this proof.
3. Complete the remaining invalid-batch and platform checks on Windows/macOS. The owner's general 0.1.8 trial is not evidence that every listed acceptance case was exercised.
4. Close 0.2.0 only after that live proof; then proceed to verified bearings and print profiles in 0.3.0. Downstream-reference stability and broader editing remain in 0.5.0.
