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

## Dialog performance

### Diagnosing slow group expansion (0.4.7)

For the Preview-off selection correction, select a face and one or more positions, wait for a valid preview, then toggle Preview off/on repeatedly. The face and every point must remain selected; Preview off must remove only temporary geometry and Apply Seats must remain usable with valid inputs. Repeat after group toggles have replayed graphics and after changing a dimension. Explicitly change/remove a face or point to ensure an old selection is not restored. Native reproduction of the old build showed a missing face, retained point and **3: invalid argument selection**. The latest correction retains source tokens from before the cut; native acceptance of the corrected build is pending.

The latest missing-preview report was inspected directly in Fusion: face/point selections remained, but the status read **Could not queue the BearingNest preview.** A native API test showed that fireCustomEvent returns False even though its handler is delivered. The latest build no longer treats this return flag as an enqueue failure. Update the full add-in and restart; select a face/point, then change shaft mode to Blind and edit its depth. Confirm that the selection remains, the preview updates, and the queue error no longer appears. Legitimate geometry/depth errors must still be shown. Complete dialog acceptance of this fix remains pending.

The owner reports that group toggles still take 1–2 seconds with an active geometry preview; shared tables gave a modest improvement. Update the complete add-in folder and restart before comparing this diagnostic revision.

1. Open BearingNest without selecting a face/positions. Toggle a parameter group a few times, then cancel.
2. Reopen, select a face/position and wait for the geometry preview. Toggle the same group a few times, then cancel.
3. Open Fusion's **Text Commands** window (under View > Panels). Each closed dialog writes a **BearingNest UI timing** summary there. Compare `changed`, `validate`, `preview`, `preview_rebuild` and `preview_replay` counts/maximum times and the recent callback sequence. Copy the summaries when reporting the delay.

Times cover Python handlers only, excluding native dialog layout and Fusion's rollback before preview callbacks. Short callback times therefore do not rule out rollback cost. Diagnostics retain only IDs/times, not entered values, and buffer data until close rather than logging during group toggles.

The owner's first trace confirmed 228–234 ms repeated preview callbacks after group toggles, with group handlers at 0.0 ms and validation at or below 0.5 ms. The current 0.4.7 revision caches a detached final-body copy after a successful new-seat preview. Group-only changes replay the copy as custom graphics after Fusion rolls back the preceding temporary cuts. The first toggle may still pay the cost of rolling back the original feature preview. Further group toggles should use graphics replay, with no fresh sketch/cut features. No native speedup is confirmed yet. Existing-batch edits still rebuild normally.

For replay acceptance, inspect the visible final cut including chamfer/shaft/inner relief, warning markers and body appearance. Add/remove positions and change parameters: each must invalidate replay and rebuild the geometry. Verify face/vertex/circular-edge selection remains possible while the copied graphic is non-selectable and the native source body stays selectable. Toggle Preview off, cancel, stop/restart and apply; the native body must regain its exact original opacity and no copied graphics may remain. Check single-command undo/redo and independent seat snapshots. Resume after command suspension: reactivation must discard the copy. If custom graphics/copy APIs fail, the normal full preview must still work. A graphics cleanup failure must block retry until cleanup succeeds rather than leave an invisible source body.

The next owner trace confirms faster replay (35.1 ms total for four calls, maximum 13.7 ms), but exposes missing preview callbacks after table-control edits until point reselection. The current correction explicitly requests Fusion's preview event after geometry-affecting table edits. With a face and point already selected, change diameter/correction, land count, shaft mode and inner-ring relief; each must update without selecting the point again. Turn Preview off/on and confirm immediate removal/rebuild. Repeat after a few group toggles have enabled graphics replay. Then cancel/apply and verify cleanup. Native confirmation is still pending. Synchronous preview requests appear nested inside changed timing; totals overlap and must not be added.

The synchronous request revision was subsequently reported to lose the selected point on value changes. The latest 0.4.7 build queues/coalesces explicit requests until Fusion is idle and preserves the selected face and all points over the host rollback/callback. Repeat the sequence above with two or more points: the selection count and order must survive every value/option edit. Rapidly edit several values; the preview must use the latest values. Deliberately remove a point, including before a queued refresh: it must stay removed. Repeat with vertex/circular-edge references, Preview off/on and a suspend/resume; retained selections must not be resolved against modified preview topology. Close or apply with a queued update: no preview may run after command cleanup. Timings now include flush_preview for the queued host request; its preview/stage times are nested and totals still overlap. These native acceptance checks remain pending.

## First geometry trial procedure

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
9. Add an unrelated feature after the batch: editing must refuse before model changes. Exact whole-batch timeline groups must remain editable, expanded or collapsed; foreign group contents and lost references must produce a restriction/repair message. Legacy multi-seat records without batch IDs may be refused. Schema-1 records migrate in memory to schema 2, preserving IDs/values and defaulting absent chamfers to zero and missing Auto flags to Manual. Verify opening/cancelling does not rewrite attributes; only successful Apply saves the new format.
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
