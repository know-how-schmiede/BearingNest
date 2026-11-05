# BearingNest roadmap

Versions are planned milestones, not implemented features or promised dates.

| Version | Scope | Completion criteria |
|---|---|---|
| 0.1.0 | Foundation | Implemented: owner template integration, version/lifecycle setup, three English tabs, integrated assets and environment documentation. Owner reported no observed errors in the 0.1.8 trial on 2026-11-03; full platform/build acceptance remains open. |
| 0.2.0 | Geometry and edit proof | Implemented contour A, shaft/inner-ring cuts, optional 45-degree chamfer and snapshot-driven whole-batch editing. Owner confirmed existing-seat and multi-seat editing in the 0.3.0 trial on 2026-11-04. Editing remains limited to the last complete batch without downstream features/groups. Specific chamfer, save/reopen, failure, cancel and undo/redo acceptance remains open. |
| 0.3.0 | Catalog and profiles | Implemented verified 623/624/625/608 size aliases, searchable/custom records with sources, named profiles, auto/manual/reset and local JSON import/export. Owner confirmed the library works on 2026-11-04; screenshots document both tabs and a valid three-position preview. Detailed profile/storage/import/export cases, further RC/MR seeds and macOS remain open. |
| 0.4.0 | Multiple seats and preview | Default-on preview, collected batch diagnostics, red invalid/blue other-position markers and amber advisory wall/floor/inter-seat probes implemented. Probes use conservative cylinders and exclude Through All shaft walls; exact minimum thickness is not claimed. Native graphics cleanup, warning behavior, invalid-batch atomicity and platform acceptance remain open. |
| 0.5.0 | Robust editing | Lost-reference handling; stable updates; schema migration; component transforms and edge cases verified. |
| 0.6.0 | Printed trials | Compare 3/5/7/9 lands, width modes and correction presets; calibrate print defaults and document results. |
| 0.9.0 | Localization and release candidate | Introduce English source locale plus German translation; terminology review; install/uninstall and Fusion resource QA; complete guidance. |
| 1.0.0 | First stable release | Required checks and manual Fusion trials pass; library sources reviewed; license/publisher/repository links decided; owner publishes. |

## Localization brought forward (0.4.1)

At the owner's request on 2026-11-05, German UI localization precedes robust editing. The owner reports that 0.4.0 runs; detailed acceptance cases remain separately open. Version 0.4.1 implements English/German dialog text selected from Fusion's language preference, with English fallback. Technical exception details and built-in profile names remain English. The 0.9.0 milestone retains terminology review and release/resource QA.

Before continuing with 0.5.0, review German layout in Fusion, including Settings/About, long wall warnings and restored batches using Durchgehend/Sackloch. Verify preview, cancel and apply; switch Fusion to English and restart to check fallback and unchanged saved data.

## Immediate next steps

The owner confirmed automatic German selection in German Fusion on 2026-11-05. Version 0.4.2 implements the requested compact dialog and named parameter saves in the catalog. Check the native button, layout and preset reload, including after reopening Fusion; automated checks do not replace this UI acceptance.

1. Run the [0.4.0 preview/wall acceptance procedure](PREVIEW_AND_WALLS.md#acceptance-in-fusion-pending) on a disposable design. Record Fusion build and OS; the owner's 0.3.0 library/edit confirmation is recorded separately.
2. Verify save/reopen discovery, stable seat IDs, repeated edits, failed updates, preview cancel and single-command undo/redo. Automated API-substitute checks do not complete this proof.
3. Complete the remaining chamfer, invalid-batch and platform checks on Windows/macOS. The owner's general 0.1.8 and library/edit 0.3.0 trials do not establish every listed acceptance case.
4. Close 0.2.0 only after that live proof. At the owner's request, 0.3.0 catalog/profile development proceeded in parallel with this pending gate; run its [catalog/profile acceptance procedure](CATALOG_AND_PROFILES.md#acceptance-in-fusion-pending). Downstream-reference stability and broader editing remain in 0.5.0.
