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

Use a disposable design. These steps are an acceptance procedure, not a report of completed live testing.

1. Create a parametric solid block, for example 60 × 60 × 20 mm, in the root component.
2. Create a sketch point at the center of its top face and finish the sketch. Keep the point visible.
3. Open BearingNest. Select the block's top face and the sketch point.
4. Use the manual example values: outside diameter 22 mm, bearing width 7 mm, diameter correction −0.10 mm, axial correction 0 mm, 5 lands, contact angle 30°, rotation 0°, relief depth 1.2 mm, radius 0.4 mm.
5. Check the displayed effective contact diameter (21.9 mm) and seat depth (7 mm).
6. Enable **Preview**. Check that the contour cuts inward, with five contact lands and rounded transitions.
7. Change a dimension and check that the preview rebuilds. Cancel and confirm that no new sketch, tool body or cut remains.
8. Reopen, repeat and click **Create Seats**. Expect a hidden contour sketch and a direct cut extrusion per seat, leaving one body. Validation tool extrusions are deleted before cutting and do not remain in the timeline.
9. Verify geometry dimensions. Undo once: the entire command should disappear. Redo and inspect the result.
10. Save/reopen a test design and verify its feature attributes using the Fusion API before claiming persistence acceptance. There is no seat edit/reopen UI yet.

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

The owner reported Position 1: The seat sketch must contain exactly one closed profile in 0.1.4. Update the complete add-in folder to 0.1.5 and restart. Repeat one point, then three points with Preview enabled. Verify the preview appears, Create Seats stays enabled, and generated sketches are hidden after cutting. Profile calculation remains enabled on those sketches. If a profile error remains, record the added found-count value.

## Invalid placement and lifecycle checks

- Dialog regression for 0.1.4: select a face and valid points with Preview off. Create Seats must enable. Enable Preview and verify the cuts appear and creation remains enabled. Disable Preview and check that the preview rolls back without disabling creation. Trigger an invalid placement, correct it, and verify recovery. No status-text updates may occur inside validateInputs.

- Try a position near the edge, insufficient material depth and a pre-existing void. The preview/creation must report an error without leaving partial geometry.
- Repeat with a bottom-facing or inclined planar face and verify that the cut follows the inward normal.
- Try 3/5/7/9 lands with feasible contact angles. Reject overlapping transitions, nonpositive depths and invalid expressions.
- Switch Preview off and cancel: the previous preview must be rolled back.
- Verify exactly three English tabs, correct logo/version, no sample palette commands and no duplicated toolbar buttons.
- Close the dialog, stop the add-in and confirm toolbar cleanup; start it again.
- Repeat on macOS before claiming verified support.

Containment compares the actual contour tool with the selected body using temporary BRep intersections. An additional 0.001 mm inward shift checks for a remaining floor; this is a numerical tolerance, not a recommended wall thickness. Thin-wall warnings and red invalid-position graphics are not implemented yet.

## Local checks

Run from the repository root:

```text
python tools/sync_version.py --check
python -m unittest discover -s tests -v
```

Tests cover contour closure/tangency, parameters and units, UI selection/callbacks, all-position validation, pairwise overlap, duplicate centers, partial batch failures, profile-fill restoration, snapshots and version consistency. The API substitute does not execute Fusion's solid kernel or prove preview cancellation/undo in the desktop app.
