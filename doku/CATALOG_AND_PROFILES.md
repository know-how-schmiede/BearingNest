# Bearing catalog and print profiles

Version 0.3.0 implements searchable seed/custom bearings, named print profiles, per-field Auto/Manual behavior and local settings persistence. On 2026-11-04 the owner confirmed the library works, and existing seats can be edited individually or in batches. [Screenshots](SCREENSHOTS.md) show both tabs and a valid three-position catalog-based preview. Detailed save/reopen, profile, import/export and platform cases remain pending; the general report does not establish every acceptance case.

## Verified seed sizes

The built-in entries are **size aliases**, not manufacturer-specific products. Principal dimensions were checked on 2026-11-04 against the bearing table in [SKF NILOS-Rings, printed page 12 / PDF page 13](https://cdn.skfmediahub.skf.com/api/public/0901d19680237e2b/pdf_preview_medium/0901d19680237e2b_pdf_preview_medium.pdf#page=13).

| Designation | Bore d (mm) | Outside D (mm) | Width B (mm) |
|---|---:|---:|---:|
| 623 | 3 | 10 | 4 |
| 624 | 4 | 13 | 5 |
| 625 | 5 | 16 | 5 |
| 608 | 8 | 22 | 7 |

No inner-ring outside/shoulder dimension is inferred from these principal dimensions or from the NILOS seal dimensions. Manufacturer and part-number fields stay empty for aliases. RC/Tamiya and MR candidates in the specification remain pending verification; they are not silently populated from unverified examples.

## Bearing Seat tab

Search accepts designation, manufacturer, part number and dimensions. All space-separated terms must match. As of 0.4.3, explicitly selecting a catalog bearing replaces every stored seat parameter in the form: dimensions, fit/axial corrections, land count/angle/rotation, radial relief, radius, chamfer, shaft mode/allowance/depth and inner-ring relief switch/diameter/depth. It also restores the stored print profile, Auto flags, bearing name and metadata editors in Settings. Stored effective values are restored exactly, without recalculating Auto fields on load. Later explicit profile changes still update Auto fields. Face/position selections and the preview switch remain command controls, independent of the bearing preset.

Built-in and older dimension-only entries have no historical seat settings to recover. Selecting one uses its d/D/B with the standard seat values (including 0.4 mm chamfer, shaft Off, inner relief disabled and bore-equal pending diameter), the packaged provisional print profile and three enabled Auto flags. This prevents settings leaking from the previously selected bearing. Unknown ring dimensions remain unknown. To retain custom fit/shaft/relief settings for future use, save a complete named preset again. Direct edits affect this command only until explicitly saved. The saved seat snapshot contains effective dimensions, original catalog dimensions, record identity, source and an override flag.

Select **Manual dimensions** to disconnect catalog provenance while retaining current dimensions. Unknown inner-ring geometry remains unknown. The existing bore-equal relief preset and explicit manual drawing-based relief diameter remain in effect; even a custom record's known ring dimension does not automatically choose an uncalibrated radial clearance.

Each print-derived field has an Auto checkbox. Editing its effective value switches that field to Manual; switching profiles changes only Auto fields. Enable Auto for one field to restore its suggestion, or use **Reset all three fields to suggested values**. No fit correction is derived from a print profile.

| Field | Provisional default formula |
|---|---|
| Radial relief depth | 3 x nozzle diameter |
| Transition radius | 1 x nozzle diameter |
| Inner-ring relief depth | 2 x layer height |

The initial profile uses a 0.4 mm nozzle and 0.2 mm layers. Profile selection, Auto checkboxes, reset and factor editors are under Settings. Positive finite inputs are required. Infeasible contours are rejected, never silently clamped. Layer counts have physical meaning only when the seat axis aligns with print Z. These suggestions still require printed trials.

The wall-warning factor starts at a provisional 2 x nozzle. In 0.3.0 this was stored for future use. Version 0.4.0 uses it for [conservative advisory margin probes](PREVIEW_AND_WALLS.md); these do not measure exact minimum wall thickness or establish a safe structural limit.

## Settings tab

Both **Save parameters to bearing catalog** below the preview status and **Save custom bearing with current d/D/B** in Settings now store a complete seat preset, profile snapshot and Auto flags. The first creates a new identity under the entered bearing name; the Settings action updates an existing custom ID or creates one when empty. Neither action silently updates existing geometry. Catalog selection fills the metadata editors automatically; the separate metadata-load action remains available.

- To create a custom bearing, set d/D/B on Bearing Seat, fill its designation and optional manufacturer, part number, source/drawing, notes and purchasing URL in Settings. Leave Custom ID empty, then use **Save custom bearing with current d/D/B**. The optional ring outside diameter uses 0 in the editor for unknown and JSON null in storage.
- To copy a seed or edit a custom record, select it on Bearing Seat and use **Load selected bearing metadata**. Seed copies receive new custom IDs; custom records retain their ID. Save updates that custom ID. Clear Custom ID to create a separate record. Seed aliases cannot be updated or deleted.
- **Delete custom bearing by ID** removes that local record. Existing seats and the active dialog retain snapshots.
- Select a print profile, change its name/nozzle/layer/factors and use **Save and use named profile**. An existing name updates that profile; a new name creates a separate one. Save also applies the profile to this dialog's Auto fields. At least one local profile must remain. Deleting a profile keeps the active dialog's stored profile and effective values; explicitly select another profile to change them.
- Import/export accepts a separate absolute `.json` path. Export requires a new destination filename. Import validates the entire document and merges by stable record identity; duplicate profile names with different IDs are rejected. An import does not change the active seat's effective values or historical snapshots. Select an imported profile/record explicitly to use it.

Save, delete and import take effect immediately in local settings. Cancelling the geometry command does not undo these explicit library actions. Unsaved editor changes are discarded. Geometry preview/cancel does not itself write settings.

## Storage and reopening

The settings file uses schema version 1, independently of seat snapshot schema and release version:

- Windows: `%APPDATA%/BearingNest/settings.json`.
- macOS: `~/Library/Application Support/BearingNest/settings.json`.

Local JSON stores custom bearings and named profiles. Built-in aliases come from the packaged code. New commands start with manual bearing dimensions and the first stored print profile; this release does not remember the last selected bearing/profile.

Writes validate first, write a sibling temporary file and atomically replace the destination. Invalid/future schemas and malformed files produce a visible load error and are preserved; settings writes are blocked until the file is repaired/moved and the command reopened. Effective seat geometry can still use manual values. URLs are stored as text and are never fetched or launched automatically.

Each committed seat stores independent bearing/profile copies and the three Auto flags. Reopening uses these snapshots even when the library changed or a record was removed. Historical effective values are not recomputed merely by opening the dialog. Current library data and historical snapshots appear as separate choices when they differ. Explicitly choose a profile or reset an Auto field to recalculate. Old 0.2.0 records have no print profile details and default to Manual for all three derived fields, preserving their geometry; the provisional profile is offered as a future suggestion.

## Acceptance in Fusion (pending)

1. Update the complete add-in folder, restart and confirm BearingNest 0.3.0 and exactly three tabs. Repeat the existing 0.2.0 geometry/edit acceptance separately.
2. Search/select each seed size and check d/D/B, source and reset to standard seat/profile values. Save two custom entries with distinct corrections, land count, shaft/relief modes and profile/Auto flags, using both save actions. Switch between them and confirm every stored field, name and metadata editor changes. Repeat after closing/reopening the command and after JSON export/import. Verify no delayed selector events recalculate loaded effective values. The bore-equal inner-ring relief remains pending rather than inventing a ring dimension.
3. Save a custom bearing with a drawing source, unknown ring diameter and optional short purchasing URL. Close/reopen the command and select it. Update it by ID, copy it to a new ID and delete the copy. Confirm built-ins cannot be overwritten.
4. Save a second profile with a 0.6 mm nozzle and 0.3 mm layers. Expect suggestions 1.8 / 0.6 / 0.6 mm. Make relief manual at 1.5 mm; switch profiles and confirm only Auto fields change. Reset one field and all fields. A profile can be dimensionally valid but generate an infeasible contour; preview must report the geometry error.
5. Create a valid batch, save/reopen the design, then modify/delete its library records and profile. Reopen the batch and confirm historical dimensions, source, profile and flags remain. Apply an explicit profile change and verify stable seat IDs, cancel and undo/redo.
6. Export to a new file; verify an existing file cannot be overwritten by Export. Import valid custom records/profiles. Reject corrupt JSON, future schemas, duplicate names/IDs, invalid dimensions and nonpositive nozzle/layer/factors without partial changes.
7. With a backed-up settings file, simulate unreadable/future-schema settings and confirm the visible error, preserved original and blocked saves. Restore the file outside the command, reopen and retry. Record Fusion build and OS; repeat on macOS before claiming platform acceptance.

Automated checks exercise validation, search, atomic file replacement, profile changes, reset, delayed UI events, metadata forwarding, snapshot isolation, legacy flags and import/export. They substitute the Fusion API and do not prove native UI or kernel behavior.
