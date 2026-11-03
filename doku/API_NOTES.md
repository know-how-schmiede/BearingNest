# API notes and validation

Official Autodesk documentation and the installed Fusion Python API definitions were checked on 2026-11-03.

## Implemented prototype

The owner's Python template still owns run/stop, command registration and retained event handlers. BearingNest is registered in `FusionSolidEnvironment / SolidCreatePanel`. The visible command name appends `VERSION` from `version.py`; IDs remain stable.

The dialog keeps exactly three tabs. The Bearing Seat tab now collects face/position selections and manual dimensions. Unit inputs use explicit mm/degrees. Fusion's internal length/angle values are converted to mm/degrees before validation, and contour coordinates are converted to cm only at the sketch API boundary.

`contour_geometry.py` is the shared pure contour implementation. The documentation SVG generator uses that same code. The Fusion adapter creates an empty face sketch with `addWithoutEdges`, then builds exact lines and three-point circular arcs. Curves are fixed in this prototype; dimensional editing is not yet implemented.

The sketch normal is compared with the outward face normal (including `isParamReversed`) to select the inward extrusion direction. A new-body extrusion produces the exact contour tool. Temporary BRep intersections compare that tool's full volume with its intersection volume inside the selected body; a second check shifts the tool inward by 0.001 mm to verify a floor. Every tool is hidden during validation. All positions and their pairwise envelope differences are checked before the first cut. Validation extrusions are then deleted, and direct cut extrusions use explicit participantBodies to affect only the selected body.

Preview is opt-in. Its handler sets `isValidResult = False`, so execute rebuilds from the original model and writes the seat snapshot on the final cut. Execute errors set `executeFailed` and `executeFailedMessage` to abort the command transaction even though the template wrapper catches exceptions. The adapter also removes newly created features on failure, including preview failures. Live rollback and cleanup still require acceptance testing.

The supported initial scope is one root-component solid body in a parametric design. Proxy/child-component placements are rejected. Multiple positions on one face share the same settings; unlimited position selection uses setSelectionLimits(1, 0). Version 0.1.6 adds optional shaft and inner-ring operations; chamfer, catalog, profile storage, red error graphics and thin-wall warnings remain pending.

Generated contour sketches remain visible with areProfilesShown enabled through profile construction and the final cut, then are hidden using isVisible=False. Their profile calculation stays enabled for feature recomputation. On successful execute, selected point sketches also have only their profile fills disabled; their points, curves and visibility remain unchanged. Failed batches restore the original fill flags. Preview does not change source sketch fill preferences. Removing retained coplanar tools and disabling profile overlays addresses possible sources of the reported triangles; the exact cause has not been established from the screenshot alone. Existing seats are not rebuilt automatically.

The 0.1.4 screenshot identifies a concrete profile-construction failure at position 1. Version 0.1.5 removes the premature profile/visibility suppression introduced in 0.1.3, restoring the 0.1.2 construction order. The profile regression substitute now depends on profile-display and deferred-compute state rather than always returning one profile. The owner confirmed preview and creation working in 0.1.5; the supplied screenshots are embedded in [the screenshot guide](SCREENSHOTS.md).

## Optional clearances in 0.1.6

Each shaft/inner-ring operation has a circular sketch with profiles enabled. Blind shaft depth starts at the selected face; inner-ring relief uses a signed OffsetStartDefinition at the seat floor. Each circle sketch independently resolves its inward normal. Through All uses ThroughAllExtentDefinition from the installed Autodesk SDK, with explicit participantBodies. Its finite validation envelope covers the projected body extent plus 1 mm and intentionally allows the shaft exit. Seat, blind shaft and inner-ring tools still require full containment and floor checks. Every tool participates in pairwise batch overlap checks before any cut. Unknown bearing inner-ring dimensions are not inferred from the manual relief diameter.

## Validation status

The 0.1.6 owner report shows a Through All preview without a shaft opening. In 0.1.7, the ThroughAllExtentDefinition's own isPositiveDirection property is explicitly set to agree with setOneSideExtent. The property was checked against the installed Autodesk Python SDK. Returned features are checked for healthy status, and every cut must reduce target-body volume. A failed feature is deleted inside the extrusion helper before the batch cleanup handles previously created geometry. These checks prevent a warning/no-op extrusion from being reported as a valid preview. Live 0.1.7 confirmation is pending.

In 0.1.4, validateInputs only sets areInputsValid; it no longer writes the status textbox or rechecks placement against temporary preview topology. Status updates run from inputChanged/preview/execute and skip unchanged text. Relevant edits and preview retries clear old errors; real placement/containment/overlap checks remain in the geometry path. This was insufficient on its own: the later 0.1.5 construction-order change resolved the reported profile failure and was confirmed by the owner.

59 automated tests pass, covering pure contour properties, parameter validation/conversion, menu registration, dialog callbacks, cleanup/error paths and snapshots. Tests use an isolated API substitute for Fusion calls. Python/API member checks were also performed against the installed SDK definitions.

The owner confirmed menu launch, version label, Solid > Create placement and working preview/creation in 0.1.5. Version 0.1.6 clearance geometry remains unverified in Fusion. Read-only UI inspection found a separate installed AddIns copy rather than the edited repository source. No installed files or user model were changed. macOS remains untested.

## Next proof

Run the [manual geometry acceptance checks](INSTALLATION.md). Verify the new shaft/inner-ring operations using [the clearance guide](SHAFT_AND_RELIEF.md). Then implement chamfer, followed by snapshot-driven reopening and editing. The [persistence notes](PERSISTENCE_PROTOTYPE.md) distinguish saved metadata from proven editable geometry. Version 0.2.0 is still an incomplete milestone.

## Official references

- [Command transactions, preview rollback and reuse](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Commands_UM.htm)
- [CommandEventArgs: execute failure and preview result](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_CommandEventArgs.htm)
- [Selection filters](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_SelectionCommandInput.htm)
- [Units](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Units_UM.htm)
- [Empty face sketches](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Sketches_addWithoutEdges.htm)
- [Three-point sketch arcs and direction](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_SketchArcs_addByThreePoints.htm)
- [Face orientation](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_BRepFace_isParamReversed.htm)
- [One-sided extrusion](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_ExtrudeFeatureInput_setOneSideExtent.htm)
- [Signed start offsets](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_OffsetStartDefinition_create.htm)
- [Extrusion start extent](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_ExtrudeFeatureInput_startExtent.htm)
- [Temporary boolean operations](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_TemporaryBRepManager_booleanOperation.htm)
- [Explicit cut participant bodies](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_ExtrudeFeatureInput_participantBodies.htm)
- [Sketch profile fill display](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Sketch_areProfilesShown.htm)
- [Unlimited position selection](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_SelectionCommandInput_setSelectionLimits.htm)
- [Attributes and updates](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Attributes_add.htm)
- [Command name](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_CommandDefinition_name.htm)
- [Toolbar icons](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/UserInterface_UM.htm)
