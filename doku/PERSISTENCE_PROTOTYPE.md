# Seat persistence prototype

Status: the snapshot codec and Fusion API adapter are now connected to the creation command. Successful execute writes one snapshot to each direct cut extrusion; preview does not persist one. Reopening/editing is not yet implemented, and save/reopen in Fusion is not yet verified.

## Implemented behavior

`seat_snapshot.py` stores a stable seat ID, independent schema version, effective parameter values, bearing/profile copies, auto/manual flags, placement reference tokens and generated feature tokens. JSON serialization detaches the snapshot from mutable catalog/profile dictionaries. Unknown bearing dimensions remain null. Parameter revisions preserve the seat ID; schema changes require explicit migration and unknown schema versions are rejected.

The prototype validates record structure, finite JSON values, Boolean auto/manual flags and nonempty reference tokens. It does not yet validate all physical geometry dimensions. Geometry validation must run before committing a real seat.

`seat_storage.py` uses the attribute group `BearingNest` and name `seat_snapshot`. Attach this attribute to the generated seat feature. Saving again updates the same attribute; replacing a different seat ID is rejected. Discovery uses entity attributes because Fusion's design search excludes attributes attached directly to Product/Document objects. Invalid records must be reported individually by the future UI.

Reference lookup uses `findEntityByToken`. A missing token or multiple matches requires repair; the prototype never chooses a split face automatically. This is intentionally stricter than taking the first match. Source dictionaries and token strings are not used as persistent object identities.

Since 0.1.3, snapshots reference the contour and direct cut feature; deleted validation tools are not persisted. The schema's feature map also remains able to read older snapshots containing a tool reference. Existing 0.1.2 seats are not rebuilt or migrated automatically.

## Remaining Fusion proof

1. Create a single seat from confirmed contour A in a disposable parametric part design, with explicit mm/degrees conversion at the API boundary.
2. Attach a snapshot to the generated feature, save the design, close and reopen it, and discover the same record.
3. Resolve placement and feature tokens. Refill the three-tab dialog from the stored snapshot; reject lost or ambiguous references with a repair message.
4. Prove an update of the existing sketch/features in one command transaction. Preserve seat ID, avoid duplicate cuts, and write the revised snapshot only after a successful geometry update. Metadata updates alone are not proof of editable geometry.
5. Prove cancel, failed update, undo/redo and save/reopen behavior in Fusion before exposing editing to users. Component transforms and assembly support still need separate validation.

The adapter itself does not implement a geometry transaction, invoke a native edit command, create custom features or claim rollback safety for future feature operations. No native timeline edit strategy is approved by these isolated tests alone.

## Official API references

- [Attributes.add: updates matching group/name; size limit](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Attributes_add.htm)
- [Design.findAttributes: entity attribute discovery](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Design_findAttributes.htm)
- [Design.findEntityByToken: zero, one or multiple matching entities](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Design_findEntityByToken.htm)

Isolated tests cover detached copies, unknown bearing values, round trips, stable identity, updates without duplicate records, corrupt/unsupported data, and missing/ambiguous tokens. Live Fusion verification is pending.
