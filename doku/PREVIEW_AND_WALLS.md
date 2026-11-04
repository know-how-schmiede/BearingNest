# Preview diagnostics and advisory wall margins

Version 0.4.0 starts Preview enabled by default, at the owner's request. It adds collected batch errors, approximate color markers and conservative wall/floor/inter-seat warnings. These additions have automated substitute coverage; native Fusion behavior still needs the checks below. The owner's confirmed 0.3.0 library and existing-seat/batch editing remain documented in [screenshots](SCREENSHOTS.md).

## Batch behavior

The command resolves all positions before preparing tools. Duplicate centers and invalid placements reject the whole batch. For positions with valid references, contour/clearance preparation collects independent containment failures and checks every pair of successfully prepared complete envelopes. A containment or overlap error blocks every cut and every snapshot write. A later cut or metadata failure still rolls back the batch.

No valid subset is silently committed. Positions whose own tool preparation failed cannot undergo further pairwise testing; repair the reported problems and preview again. Unexpected API/kernel errors can stop further diagnostics and remain blocking errors.

When a batch is rejected, its validation features are removed and custom graphics show the approximate candidate envelopes:

| Color | Meaning |
|---|---|
| Red | Invalid placement, breakout, insufficient floor, duplicate center or conflicting seat |
| Blue | Other resolved positions in the rejected batch; these are not an independent promise of validity |
| Amber | Advisory wall/floor/inter-seat warning on an otherwise valid preview |

The circle and cross use the contact radius plus radial relief and chamfer. They are approximate location/envelope markers, not the exact relief contour or a successful cut. They follow the selected face plane, including reversed/inclined faces. The text identifies selection-order position numbers and reasons. Missing/unsupported references may have text without a drawable location. If drawing graphics fails, text diagnostics still apply and invalid geometry remains blocked.

Successful previews retain the native cut preview, with amber markers only where warnings exist. Markers are nonselectable, use centimetres at the Fusion boundary and are visible through other geometry. The dialog owns its graphics group and removes it on input changes, Preview off, another preview, execution, command destruction/cancel and add-in stop. Failed deletion retains ownership for retry and reports an error.

Preview is always rebuilt during execute so snapshots cannot be skipped. Turning Preview off prevents preview model work and removes markers. Full geometry validation and advisory checks still run during Apply Seats. Leave Preview enabled to review the warnings before committing.

## Conservative wall probes

The selected print profile supplies `wall_factor x nozzle_mm`, initially a **provisional 2 x 0.4 = 0.8 mm**. The Settings label is **Advisory wall margin / nozzle factor**. The value is copied with the profile into each seat snapshot; editing a historical batch uses its stored profile until another profile is explicitly selected.

Before cutting, temporary BRep cylinders enclose the seat, chamfer, blind shaft and effective inner-ring relief. Each radius is enlarged by the warning threshold, and its inward depth is extended by that threshold. The cylinder starts at the intended opening plane: the selected face for seat/chamfer/blind shaft, the seat floor for inner-ring relief. No extra margin is requested above an intentional opening.

Probes are tested against the original target body and the other proposed seats' complete cut envelopes. A probe crossing the outer boundary or an existing void produces a possible wall/floor warning. Intersections with another candidate envelope identify both seats. Probe/kernel failures report that advisory checking was unavailable; they do not reject otherwise valid cuts.

These enclosing cylinders are deliberately conservative. Relief gaps and the combined radial/axial margin can generate warnings where the true contour has more material. **The result is not an exact minimum wall measurement, a strength calculation or a safe printing limit.** No warning is not a structural guarantee. The user remains responsible for material, loads, orientation and slicer settings.

Native **Through All** shaft exits are intentional and are excluded from these wall probes. Lateral wall thickness along the through-shaft is also not evaluated in this version. Seat-floor and inner-ring-relief probes still run, independently of that exclusion. Existing strict containment/overlap checks are unchanged in purpose: an actual unintended breakout or conflicting cut is an error, regardless of warnings.

## Acceptance in Fusion (pending)

1. Copy the complete add-in folder, restart and confirm **BearingNest 0.4.0**. Open the command and verify Preview starts on. With no selections it must create no geometry. Select one valid face and several points; check one shared native preview. Repeat on reversed and inclined faces.
2. Mix valid positions with two independent edge/floor failures. Require text for each detected failure, red markers at those positions and blue approximate markers for the other resolved positions. The target body and permanent timeline must remain unchanged.
3. Select duplicate centers and overlapping seats. Both members of every detected conflicting pair must be marked red. Remove/correct the problem and check that markers and old error text clear and creation becomes available again.
4. Use a large block and separated seats as the no-warning control. Then put a fully contained seat close to an edge/floor or another seat within the selected profile's margin. Expect amber markers and advisory text, with Apply Seats still available. Verify the text uses the stored profile's threshold during editing.
5. Change the profile's wall factor and compare warnings. Include chamfer, blind shaft and actual floor-referenced inner-ring relief. A deliberate Through All exit must not itself produce a floor-breakout error or a through-shaft wall warning. Inspect through-shaft lateral walls manually.
6. Toggle Preview off, change values, toggle back on, then Cancel. Check no custom graphics, new sketches, validation bodies, cuts or snapshots remain. Repeat after an invalid preview, after a warning preview and while editing an existing batch. Stop/restart the add-in while the dialog is open and check marker cleanup.
7. Apply a warning-only valid batch. Inspect all cuts, feature health and saved snapshots. For a deliberately invalid batch, require no partial permanent cuts. Cause a later operation failure and verify full rollback. Undo/redo a successful creation and edit once; inspect body count and stable IDs.
8. Repeat save/reopen and the remaining [chamfer/edit](INSTALLATION.md#020-chamfer-and-edit-acceptance) and [catalog/profile](CATALOG_AND_PROFILES.md#acceptance-in-fusion-pending) checks. Record OS and Fusion build and repeat on macOS before claiming platform acceptance.

Automated tests cover aggregate error attribution, cleanup before any cut, advisory failures, unit/depth references, inter-seat warnings, marker plane math/colors/ownership and default-on/off UI lifecycle. They substitute the API; no native rendering/kernel/cancel acceptance is claimed.
