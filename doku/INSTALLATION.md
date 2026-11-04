# Installation and verification

## Environment

Target: Autodesk Fusion desktop on Windows or macOS with its bundled Python API. This prototype requires a parametric design with design history enabled, a solid body in the root component, and a planar seat face. Assembly-context geometry and child-component geometry are rejected.

The manifest enables both platforms, but macOS and current geometry behavior still require live checks. No minimum supported Fusion build is claimed.

## Update or register

1. Stop BearingNest in Fusion's **Utilities > Add-Ins > Scripts and Add-Ins** dialog.
2. Update the complete `Fusion-Add-In/BearingNest` folder used by Fusion. Include all Python modules, the manifest, command resources and `lib`. Do not copy only `BearingNest.py`.
3. If already installed in Fusion's AddIns folder, replace the contents of that BearingNest copy with the updated source. Alternatively, register the repository's BearingNest folder directly as an existing add-in.
4. Start BearingNest. Confirm the manifest and menu show the current version from `version.py`.
5. Open **Solid > Create >** `BearingNest <VERSION>`.

Fusion UI labels vary by version/language. See [Autodesk's installation guide](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/How-to-install-an-ADD-IN-and-Script-in-Fusion-360.html).

During inspection on 2026-11-03, the running add-in referenced a separate copy at `%APPDATA%/Autodesk/Autodesk Fusion 360/API/AddIns/BearingNest`. Restarting that copy does not automatically load repository edits. No installed files were changed by the agent.

## First geometry trial

The owner confirmed preview/creation in 0.1.5, shaft/relief in 0.1.7, and library use plus existing-seat/batch editing in 0.3.0. [Screenshots](SCREENSHOTS.md) record these versions. Follow the [clearance test guide](SHAFT_AND_RELIEF.md) and the new [0.4.0 preview/wall acceptance procedure](PREVIEW_AND_WALLS.md#acceptance-in-fusion-pending). Keep Shaft opening set to Off to repeat the seat-only trial below.

Use a disposable design. These steps are an acceptance procedure, not a report of completed live testing.

1. Create a parametric solid block, for example 60 × 60 × 20 mm, in the root component.
2. Create a sketch point at the center of its top face and finish the sketch. Keep the point visible.
3. Open BearingNest. Select the block's top face and the sketch point.
4. Use the manual example values: outside diameter 22 mm, bearing width 7 mm, diameter correction −0.10 mm, axial correction 0 mm, 5 lands, contact angle 30°, rotation 0°, relief depth 1.2 mm, radius 0.4 mm.
5. Check the displayed effective contact diameter (21.9 mm) and seat depth (7 mm).
6. **Preview** starts enabled in 0.4.0. Check that the contour cuts inward, with five contact lands and rounded transitions. Toggle it off/on and verify the preview is removed/rebuilt.
7. Change a dimension and check that the preview rebuilds. Cancel and confirm that no new sketch, tool body or cut remains.
8. Reopen, repeat and click **Apply Seats**. Expect a hidden contour sketch and a direct cut extrusion per seat, leaving one body. Validation tool extrusions are deleted before cutting and do not remain in the timeline.
9. Verify geometry dimensions. Undo once: the entire command should disappear. Redo and inspect the result.
10. Save/reopen a test design and verify its feature attributes using the Fusion API before claiming persistence acceptance. Version 0.2.0 adds an edit/reopen list; follow the acceptance procedure below.

The depth is measured from the selected face: width + axial correction. Positive correction recesses the bearing; negative correction makes it protrude. Pattern rotation is relative to the generated sketch's local X axis.

## Multiple positions and triangle regression

1. On a disposable 60 x 60 x 20 mm block, create two sketch points on the same face, 30 mm apart and each at least 15 mm from the outer edges. With the example dimensions above, the seats fit without overlapping.
2. Select one face and both points in the Seat positions input. Check the reported position count, preview both seats, cancel and verify that no cuts or contour sketches remain.
3. Repeat and create the batch. Confirm two cuts, two hidden contour sketches, one target body and no retained validation extrusion or tool body.
4. Before creating, enable profile fills on the placement sketch. After creating, check that its points and curves remain visible while profile fills are disabled. Compare the formerly triangulated areas while orbiting the model; report any remaining artifacts. Preview leaves the source sketch's profile-fill preference unchanged.
5. Add a third point that causes breakout or overlaps another seat. Creation/preview must reject the entire batch, identifying the position(s), without retaining any cut. Remove the bad point and retry.
6. Select two distinct entities with the same center. Confirm duplicate-center rejection before feature creation.
7. Undo a successful batch once and verify that all its seats are removed. Check display restoration on cancel, failure and undo in Fusion.

The owner confirmed single-seat creation in 0.1.2 but reported triangles on surrounding faces. The 0.1.3 change replaces retained tool/combine geometry with direct cuts and removes coplanar profile fills. The screenshot alone does not establish the cause; this regression check is still required. Existing seats are not automatically rebuilt. For a diagnostic on an old seat, manually hide the source placement sketch or disable its profile display and check whether the triangles disappear.

## Profile regression in 0.1.5

The owner reported Position 1: The seat sketch must contain exactly one closed profile in 0.1.4. The owner confirmed this regression fixed in 0.1.5. Update the complete add-in folder to the current version and restart when repeating the test. Repeat one point, then three points with Preview enabled. Verify the preview appears, Create Seats stays enabled, and generated sketches are hidden after cutting. Profile calculation remains enabled on those sketches. If a profile error remains, record the added found-count value.

## Invalid placement and lifecycle checks

- For 0.1.8, verify face-to-position focus transfer and the bore-prefilled inner-ring pending state using the [clearance guide](SHAFT_AND_RELIEF.md). The bore preset must allow the seat/shaft preview without creating a separate relief cut.

- Dialog regression for 0.1.4: select a face and valid points with Preview off. Create Seats must enable. Enable Preview and verify the cuts appear and creation remains enabled. Disable Preview and check that the preview rolls back without disabling creation. Trigger an invalid placement, correct it, and verify recovery. No status-text updates may occur inside validateInputs.

- Try a position near the edge, insufficient material depth and a pre-existing void. The preview/creation must report an error without leaving partial geometry.
- Repeat with a bottom-facing or inclined planar face and verify that the cut follows the inward normal.
- Try 3/5/7/9 lands with feasible contact angles. Reject overlapping transitions, nonpositive depths and invalid expressions.
- Switch Preview off and cancel: the previous preview must be rolled back.
- Verify exactly three English tabs, correct logo/version, no sample palette commands and no duplicated toolbar buttons.
- Close the dialog, stop the add-in and confirm toolbar cleanup; start it again.
- Repeat on macOS before claiming verified support.

Containment compares the actual contour tool with the selected body using temporary BRep intersections. An additional 0.001 mm inward shift checks for a remaining floor; this is a numerical tolerance, not a recommended wall thickness. Thin-wall warnings and red invalid-position graphics are not implemented yet.

## 0.2.0 chamfer and edit acceptance

The owner reported no observed errors in a general 0.1.8 trial on 2026-11-03, then confirmed existing-seat and multi-seat editing in the 0.3.0 trial on 2026-11-04. Detailed chamfer, save/reopen, failure, cancel and undo/redo cases and the Fusion build were not supplied. Remaining checks below are not all established by that general feedback.

1. Update the complete add-in folder and confirm the current BearingNest version (0.4.0 includes these 0.2.0 operations). In a disposable root-component block, choose **Create new seats** and select one face and two visible sketch points.
2. Start with chamfer 0 mm to repeat the accepted baseline. Try 0.2, 0.4 and 0.6 mm with feasible contour settings. Preview the full rim, including relief transitions. Measure equal axial/radial legs and unchanged seat-floor depth. Cancel and confirm no geometry remains. Repeat on bottom-facing/inclined planar faces.
3. Create a valid batch with chamfer and optional shaft/relief. Check healthy features, one target body and no validation tools or chamfer-envelope sketch left behind. An impossible chamfer must reject the whole batch.
4. Test near a body edge and near another seat. The conservative cylinder (diameter contact + 2 * relief + 2 * chamfer, depth chamfer) must reject breakout/overlap before cutting. It can reject placements that the exact chamfer could fit; reduce chamfer or increase spacing.
5. Save, close and reopen the design. Choose its batch from **Create or edit seats**. Confirm restored dimensions, shaft mode, land count and manual relief override. Face/position selectors are hidden in edit mode; the command button is **Apply Seats**.
6. Change diameter, rotation and depth; preview and cancel. Verify original cuts, sketches, visibility, unsuppressed originals and unchanged snapshot values. Also switch Preview off before cancelling.
7. Apply an edit. Confirm all positions update, seat IDs remain stable and snapshots contain revised feature references. There must be no duplicate seats or suppressed originals. Repeat with chamfer, shaft and relief enabled/disabled; save/reopen again.
8. Cause an invalid update (oversized diameter, excessive depth, impossible chamfer). Require a clear error and the original batch intact after failure/cancel. Correct and retry. Undo one successful edit once, redo and inspect geometry and snapshot IDs.
9. Add an unrelated feature after the batch: editing must refuse before model changes. Repeat with grouped timeline entries and lost references; expect a restriction/repair message. Legacy multi-seat records without batch IDs may be refused. Old single-seat schema-1 records default to zero chamfer.
10. Record OS, Fusion build, values and results. Repeat on macOS before claiming platform acceptance.

Editing rebuilds only the last complete batch without downstream features or timeline groups. Placement changes, native timeline double-click editing and downstream-reference repair are outside this proof. See [persistence and editing](PERSISTENCE_PROTOTYPE.md).

## Local checks

Version 0.3.0 also needs the [catalog/profile acceptance checks](CATALOG_AND_PROFILES.md#acceptance-in-fusion-pending). Its development does not close the 0.2.0 live geometry/edit gate.

Run from the repository root:

```text
python tools/sync_version.py --check
python -m unittest discover -s tests -v
```

Tests cover contour closure/tangency, parameters and units, UI selection/callbacks, all-position validation, pairwise overlap, duplicate centers, partial batch failures, profile-fill restoration, chamfer rim selection/preflight, batch discovery/edit guards, failed-preview restoration, legacy defaults, stable snapshots and version consistency. The API substitute does not execute Fusion's solid kernel or prove preview cancellation/undo in the desktop app.
