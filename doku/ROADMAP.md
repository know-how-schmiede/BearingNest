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

The owner confirmed the latest 0.4.7 preview/selection flow works. Version 0.4.8 changes only shared form column widths to 2:1 (label/control); check label readability and usable value-field widths in Fusion, including German profile factors and catalog fields.

Preview-off face loss was reproduced natively in 0.4.7 (point retained, "3: invalid argument selection"). Source-selection tokens are now captured before preview cuts and retained across toggles, with explicit selection changes invalidating their baselines. Verify repeated Preview off/on after fresh feature previews and graphics replays, retaining face/all points and allowing Apply Seats while Preview is off. The new native test was cancelled without permanent geometry; corrected-build acceptance is pending.

Native inspection of the missing-preview report found "Could not queue the BearingNest preview." The owner's Fusion host returns False from fireCustomEvent even when the handler is later delivered. Version 0.4.7 now retains pending work until delivery and retains the CustomEvent object/handlers. Re-test value/Blind-mode changes after updating the full add-in: selections must remain, previews must rebuild, and the false queue error must disappear. The API mismatch is confirmed natively; complete corrected-dialog acceptance remains pending.

The subsequent 0.4.7 trace confirms fast graphics replay (maximum 6.4 ms) but the owner reports lost point selection on value changes. The latest correction defers/coalesces explicit preview requests through Fusion's idle/custom-event queue and restores captured face/point selections only across that preview transition. Native selection changes cancel pending restoration. Verify multiple points, circle/vertex references, deliberate deselection, rapid edits, Preview off/on, cancel/apply/undo and event cleanup; native confirmation is pending.

The latest 0.4.7 owner trace confirms faster graphics replay (four calls, 35.1 ms total, 13.7 ms maximum) but shows missing preview callbacks after table-field edits until point reselection. Geometry-affecting input changes now explicitly request Fusion's preview event with a recursion guard. Verify automatic refresh without reselection, including Preview off/on after group replay; native correction acceptance remains pending.

Version 0.4.7 now shares 9 layout tables across 42 rows instead of using one table per row. Compare group expansion speed in Fusion; the container-count reduction and regression tests do not establish a measured native speedup.

The owner reports a modest improvement, with remaining 1–2 second toggles only while geometry preview is active. The supplied trace confirms repeated 228–234 ms preview handlers after group toggles. The current 0.4.7 revision replays a detached validated new-seat body as graphics after layout-only changes, invalidating it on parameter/selection edits and reactivation. Execute always rebuilds. Existing-batch edits retain normal previews. Compare preview_rebuild/preview_replay timings and complete the graphics/opacity/selection/cancel/undo acceptance in INSTALLATION.md; native speedup is not yet confirmed.

Version 0.4.6 makes bearing dimensions the only initially expanded groups, uses 50:50 label/control rows and adds bilingual tooltips. The follow-up layout revision retains version 0.4.6, aligns contact-land/shaft selectors and provisionally moves Preview/Inner-ring relief checkboxes to the right column. Verify both languages at narrow and wide Fusion dialog sizes, including short labels/full tooltips, group expansion, expression editing and preview/edit behavior. Review checkbox placement before deciding whether to retain it.

Version 0.4.5 adds known catalog inner-ring diameter suggestions without extra clearance. Verify selection with known/unknown ring dimensions, manual overrides and preservation of existing seat snapshots in Fusion.

Version 0.4.4 reorganizes the UI at the owner's request on 2026-11-07: four tabs, grouped seat controls, an independent catalog editor, general print-profile/data management and Info links. Verify German/English native layout, catalog create/update/delete (including failed saves), separation from active seat settings and hyperlink opening in Fusion before accepting the UI change.

The owner confirmed automatic German selection in German Fusion on 2026-11-05. Version 0.4.2 implements the requested compact dialog and named parameter saves in the catalog. Check the native button, layout and preset reload, including after reopening Fusion; automated checks do not replace this UI acceptance.

1. Run the [0.4.0 preview/wall acceptance procedure](PREVIEW_AND_WALLS.md#acceptance-in-fusion-pending) on a disposable design. Record Fusion build and OS; the owner's 0.3.0 library/edit confirmation is recorded separately.
2. Verify save/reopen discovery, stable seat IDs, repeated edits, failed updates, preview cancel and single-command undo/redo. Automated API-substitute checks do not complete this proof.
3. Complete the remaining chamfer, invalid-batch and platform checks on Windows/macOS. The owner's general 0.1.8 and library/edit 0.3.0 trials do not establish every listed acceptance case.
4. Close 0.2.0 only after that live proof. At the owner's request, 0.3.0 catalog/profile development proceeded in parallel with this pending gate; run its [catalog/profile acceptance procedure](CATALOG_AND_PROFILES.md#acceptance-in-fusion-pending). Downstream-reference stability and broader editing remain in 0.5.0.
