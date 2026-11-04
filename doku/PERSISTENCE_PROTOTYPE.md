# Seat persistence prototype

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

The adapter resolves every generated feature uniquely and requires its full set to occupy the end of the ungrouped timeline with the marker at the end. Later features, groups, missing or ambiguous entities and incomplete ownership block editing before model changes. References are resolved again after suppressing original cuts, when the original placement face is restored.

Original cuts are suppressed in reverse timeline order. The existing batch constructor then validates all new tools and positions and creates replacement geometry. A failed preview cleans up the new geometry and restores the original suppression state. A successful preview is temporary and Fusion rolls it back before another preview/execute or on cancel. Execute saves revised snapshots and removes original features only after replacement creation succeeds. Any execute failure sets executeFailed to abort the whole command transaction. This is an explicit rebuild strategy, not native timeline double-click editing; downstream feature references are deliberately unsupported until the robust-editing milestone.

## Remaining Fusion proof

1. Create a batch with chamfer, shaft and relief. Record seat IDs and parameter snapshots; save, close and reopen the design.
2. Choose the batch in BearingNest and confirm the dialog restores the values and manual override behavior.
3. Change diameter, rotation and depth; preview, cancel and confirm the original geometry and metadata remain unchanged.
4. Apply an edit and confirm stable seat IDs, revised geometry, no duplicate records or cuts, and no suppressed originals left behind.
5. Turn optional chamfer/shaft/relief operations on and off across successive edits. Save/reopen again.
6. Try an invalid update and missing/ambiguous references; require repair or a clear error without partial results.
7. Check one-command undo/redo and reject editing with later features or grouped timeline entries.

These are acceptance instructions, not completed live test results. Component transforms, lost-reference repair and editing with downstream features remain later work.

## Official API references

- [Attributes.add: updates matching group/name; size limit](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Attributes_add.htm)
- [Design.findAttributes: entity attribute discovery](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Design_findAttributes.htm)
- [Design.findEntityByToken: zero, one or multiple matching entities](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Design_findEntityByToken.htm)

Isolated tests cover detached copies, unknown bearing values, round trips, stable identity, updates without duplicate records, corrupt/unsupported data, and missing/ambiguous tokens. The owner confirmed existing-seat/batch editing in the 0.3.0 trial; detailed live save/reopen, failure, cancel and undo/redo verification remains pending.
