# Seat persistence prototype

## 0.5.2: edit-preview stability work

The owner confirmed earlier-group editing works, then reported a native Fusion crash while changing values/in preview with multiple seats in one group, and a slow dialog. The cause has not been reproduced or isolated. Version 0.5.2 guards preview/model-building against recursive callbacks and extends transient final-body caching to existing-seat previews when every discovered batch references the same uniquely resolved body. After host rollback, replay resolves the original saved body reference and displays the detached result; group toggles and duplicate unchanged preview callbacks do not rebuild the sequence. Appearance/graphics cleanup remains owned by the dialog. Multiple bodies or unsupported graphics fall back to feature previews. Changed values still rebuild the affected sequence, and Apply always validates/rebuilds/persists.

Native acceptance is pending: repeat the reported multi-seat value edits and group toggles on a copy; verify retained seats, preview freshness, source opacity, Preview off/on, cancellation, apply and undo. Compare preview_replay and preview_rebuild timings. Automated guard/cache tests do not establish crash resolution.

## 0.5.1: earlier-batch editing

Choose an earlier batch in Seat mode to rebuild it and every following BearingNest batch together. Planning proves a contiguous owned timeline suffix and independent placement references before changes. Unrelated features or interleaved placement sketches in that suffix, foreign group contents, unresolved references and existing suppression block the update. Expanded/collapsed groups and ungrouped legacy batches with complete ownership are supported.

All affected cuts are suppressed from last to first. Capture source-reference tokens before replacement cuts, then rebuild chronologically. Only the selected batch receives changed values/catalog/profile options. Successors retain stored parameters, metadata, Auto flags and seat/batch IDs. Positions/faces must resolve uniquely after each preceding replacement; split faces are never guessed.

Originals remain until every replacement succeeds. Failed previews remove successful partial replacements and restore suppression/profile display. Fusion rolls back successful previews. Execute deletes originals, calls Compute All, verifies replacement validity/health and restores separate named groups in order. Execute failure aborts the whole transaction. Earlier-batch previews rebuild every affected group and may take longer. This strategy does not preserve arbitrary external references to regenerated feature entities.

Native trial, pending: use a design copy with three batches and independent source sketch points on several faces. Edit first, middle and last batches. Confirm selected-only value changes, unchanged successor values/IDs, named groups in order and no suppressed originals. Repeat expanded/collapsed groups, Preview off/on, cancel, optional shaft/relief/chamfer changes, save/reopen and one-command undo/redo. Make an early seat conflict with a later seat: require rejection and intact originals. Add an unrelated later extrusion or foreign group member: require refusal before changes. Record Fusion build and OS. Automated tests do not complete this trial.

## 0.5.0: robust-editing foundation

New snapshots use seat schema 2. The reader explicitly migrates schema 1 into a detached copy: it preserves existing seat/batch IDs and all recorded dimensions and metadata, adds a missing legacy chamfer as 0 mm and missing Auto flags as Manual. A record without a batch ID uses its own seat ID; it is never automatically merged with neighboring seats. Unknown fields and unknown bearing dimensions survive unchanged. Future schemas and malformed records are rejected. Settings JSON keeps its independent schema 1.

Opening or previewing a design does not rewrite legacy attributes. Only successful Apply saves revised schema-2 snapshots. Generated feature tokens are checked together before suppression; diagnostics identify seat and role, and missing/split/invalid entities block rebuilding. Batches with mixed identities or inconsistent effective parameters are rejected. After suppressing the originals, placement references are resolved again and the face's body must match the saved body. Failure restores original suppression state.

Use a copy of a saved 0.4.9 design for the migration trial. Earlier add-in versions reject schema-2 records after a migrated edit is applied; no downgrade conversion is provided.

Committed batches can occupy an exact whole-batch timeline group, expanded or collapsed, since 0.4.9. Later features or foreign group contents still block editing. The owner confirmed grouping works; detailed migration/edit/cancel/save/reopen/undo verification remains pending. Explicit reference reassignment, component transforms and downstream-reference stability are not implemented in this first increment.

## Historical implementation

Version 0.3.0 adds [catalog/profile snapshots and local settings](CATALOG_AND_PROFILES.md). New seats copy effective bearing dimensions, original catalog dimensions, source metadata, named profile data and the three derived-field Auto flags. Reopening uses stored values without recalculating from the current library. Older records preserve their geometry with these flags defaulting to Manual. Seat schema remains version 1 because these are additions inside existing object sections; settings files have an independent schema version 1.

Status: the snapshot codec and Fusion API adapter are connected to the creation command. Successful execute writes one snapshot to each direct cut extrusion; preview does not persist one. Version 0.2.0 added discovery, dialog reloading and constrained whole-batch editing. On 2026-11-04 the owner confirmed editing existing seats, including multiple seats together, in the 0.3.0 trial. Specific save/reopen, failure recovery, cancel and undo/redo cases still require recorded acceptance.

## Implemented behavior

`seat_snapshot.py` stores a stable seat ID, independent schema version, effective parameter values, bearing/profile copies, auto/manual flags, placement reference tokens and generated feature tokens. JSON serialization detaches the snapshot from mutable catalog/profile dictionaries. Unknown bearing dimensions remain null. Parameter revisions preserve the seat ID; schema changes require explicit migration and unknown schema versions are rejected.

The prototype validates record structure, finite JSON values, Boolean auto/manual flags and nonempty reference tokens. Physical validation runs through SeatParameters before creation or update. Optional batch identities are validated without changing schema version 1.

`seat_storage.py` uses the attribute group `BearingNest` and name `seat_snapshot`. Attach this attribute to the generated seat feature. Saving again updates the same attribute; replacing a different seat ID is rejected. Discovery uses entity attributes because Fusion's design search excludes attributes attached directly to Product/Document objects. Invalid records are reported in the dialog while valid records remain discoverable.

Reference lookup uses `findEntityByToken`. A missing token or multiple matches requires repair; the prototype never chooses a split face automatically. This is intentionally stricter than taking the first match. Source dictionaries and token strings are not used as persistent object identities.

Since 0.1.3, snapshots reference the contour and direct cut feature; deleted validation tools are not persisted. The schema's feature map also remains able to read older snapshots containing a tool reference. Existing 0.1.2 seats are not rebuilt or migrated automatically.

Version 0.1.6 snapshots include shaft mode, actual manual bore, allowance, blind depth, inner-ring clearance values and all added cut/sketch tokens. The bearing's unknown inner-ring outside dimension stays null; a clearance diameter is not a catalog bearing dimension.

## Editing implementation in 0.2.0

Open BearingNest and use **Create or edit seats** to choose a saved batch. The dialog refills dimensions, land count, shaft mode, relief settings and auto/manual relief state. Editing applies shared values to all positions in that batch; changing placement is outside this initial edit proof.

New schema-1 records carry an optional batch_id. Seat IDs remain unchanged on update. Bearing/profile metadata survives, effective manual dimensions and feature references are revised, and the relief auto/manual flag is saved. Older records without chamfer_mm default to zero chamfer. Records without batch identities are treated as individual seats: an old multi-seat creation generally cannot satisfy the complete-tail guard and may need recreation. Legacy retained-tool/combine seats are rejected.

The adapter resolves every generated feature uniquely and requires its full set to occupy the end of the timeline with the marker at the end. Since 0.4.9, an exact whole-batch group is supported. Later features, foreign group contents, missing or ambiguous entities and incomplete ownership block editing before model changes. References are resolved again after suppressing original cuts, when the original placement face is restored.

Original cuts are suppressed in reverse timeline order. The existing batch constructor then validates all new tools and positions and creates replacement geometry. A failed preview cleans up the new geometry and restores the original suppression state. A successful preview is temporary and Fusion rolls it back before another preview/execute or on cancel. Execute saves revised snapshots and removes original features only after replacement creation succeeds. Any execute failure sets executeFailed to abort the whole command transaction. This is an explicit rebuild strategy, not native timeline double-click editing; downstream feature references are deliberately unsupported until the robust-editing milestone.

## Remaining Fusion proof

1. Create a batch with chamfer, shaft and relief. Record seat IDs and parameter snapshots; save, close and reopen the design.
2. Choose the batch in BearingNest and confirm the dialog restores the values and manual override behavior.
3. Change diameter, rotation and depth; preview, cancel and confirm the original geometry and metadata remain unchanged.
4. Apply an edit and confirm stable seat IDs, revised geometry, no duplicate records or cuts, and no suppressed originals left behind.
5. Turn optional chamfer/shaft/relief operations on and off across successive edits. Save/reopen again.
6. Try an invalid update and missing/ambiguous references; require repair or a clear error without partial results.
7. Check one-command undo/redo, accept exact whole-batch groups expanded/collapsed, and reject editing with later features or foreign group contents.

These are acceptance instructions, not completed live test results. Component transforms, lost-reference repair and editing with downstream features remain later work.

## Official API references

- [Attributes.add: updates matching group/name; size limit](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Attributes_add.htm)
- [Design.findAttributes: entity attribute discovery](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Design_findAttributes.htm)
- [Design.findEntityByToken: zero, one or multiple matching entities](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Design_findEntityByToken.htm)

Isolated tests cover detached copies, unknown bearing values, round trips, stable identity, updates without duplicate records, corrupt/unsupported data, and missing/ambiguous tokens. The owner confirmed existing-seat/batch editing in the 0.3.0 trial; detailed live save/reopen, failure, cancel and undo/redo verification remains pending.
