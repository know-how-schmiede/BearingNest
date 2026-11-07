# API notes and validation

Official Autodesk documentation and the installed Fusion Python API definitions were checked on 2026-11-03.

## Implemented prototype

The owner's Python template still owns run/stop, command registration and retained event handlers. BearingNest is registered in `FusionSolidEnvironment / SolidCreatePanel`. The visible command name appends `VERSION` from `version.py`; IDs remain stable.

The dialog has four tabs: Bearing Seat, Bearing Catalog, Settings and Info. Bearing Seat collects face/position selections and manual dimensions. Unit inputs use explicit mm/degrees. Fusion's internal length/angle values are converted to mm/degrees before validation, and contour coordinates are converted to cm only at the sketch API boundary.

For 0.4.6, Autodesk's [ValueCommandInput properties](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_ValueCommandInput.htm), [table creation and column ratios](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_CommandInputs_addTableCommandInput.htm), [table cell assignment](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_TableCommandInput_addCommandInput.htm) and [table presentation styles](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_TablePresentationStyles.htm) were checked on 2026-11-07. Value inputs have no documented pixel-width setter. Numeric rows therefore use full-width transparent tables with 50:50 label/value columns, a read-only string label and the original ValueCommandInput in the second cell. The same layout helper also places land-count/shaft-mode dropdowns and the provisional Preview/Inner-ring relief checkboxes in the right column. SelectionCommandInputs remain outside tables, as required by the API. Each table displays exactly one row and no grid. Both cells expose localized tooltip text. This preserves expression handling and input IDs; native Fusion rendering at narrow sizes remains unverified.

`contour_geometry.py` is the shared pure contour implementation. The documentation SVG generator uses that same code. The Fusion adapter creates an empty face sketch with `addWithoutEdges`, then builds exact lines and three-point circular arcs. Curves are fixed; version 0.2.0 edits by rebuilding the last complete creation batch from its snapshot.

The sketch normal is compared with the outward face normal (including `isParamReversed`) to select the inward extrusion direction. A new-body extrusion produces the exact contour tool. Temporary BRep intersections compare that tool's full volume with its intersection volume inside the selected body; a second check shifts the tool inward by 0.001 mm to verify a floor. Every tool is hidden during validation. All positions and their pairwise envelope differences are checked before the first cut. Validation extrusions are then deleted, and direct cut extrusions use explicit participantBodies to affect only the selected body.

Preview starts enabled in 0.4.0 and can be switched off. Its handler sets `isValidResult = False`, so execute rebuilds from the original model and writes the seat snapshot on the final cut. Execute errors set `executeFailed` and `executeFailedMessage` to abort the command transaction even though the template wrapper catches exceptions. The adapter also removes newly created features on failure, including preview failures. Live rollback and cleanup still require acceptance testing.

The supported scope is one root-component solid body in a parametric design. Proxy/child-component placements are rejected. Multiple positions on one face share the same settings; unlimited position selection uses setSelectionLimits(1, 0). Version 0.1.6 added optional shaft and inner-ring operations, 0.2.0 optional chamfer and constrained batch editing, 0.3.0 catalog/profile storage, and 0.4.0 diagnostic markers and conservative advisory wall probes.

Generated contour sketches remain visible with areProfilesShown enabled through profile construction and the final cut, then are hidden using isVisible=False. Their profile calculation stays enabled for feature recomputation. On successful execute, selected point sketches also have only their profile fills disabled; their points, curves and visibility remain unchanged. Failed batches restore the original fill flags. Preview does not change source sketch fill preferences. Removing retained coplanar tools and disabling profile overlays addresses possible sources of the reported triangles; the exact cause has not been established from the screenshot alone. Existing seats are not rebuilt automatically.

The 0.1.4 screenshot identifies a concrete profile-construction failure at position 1. Version 0.1.5 removes the premature profile/visibility suppression introduced in 0.1.3, restoring the 0.1.2 construction order. The profile regression substitute now depends on profile-display and deferred-compute state rather than always returning one profile. The owner confirmed preview and creation working in 0.1.5; the supplied screenshots are embedded in [the screenshot guide](SCREENSHOTS.md).

## Optional clearances in 0.1.6

Each shaft/inner-ring operation has a circular sketch with profiles enabled. Blind shaft depth starts at the selected face; inner-ring relief uses a signed OffsetStartDefinition at the seat floor. Each circle sketch independently resolves its inward normal. Through All uses ThroughAllExtentDefinition from the installed Autodesk SDK, with explicit participantBodies. Its finite validation envelope covers the projected body extent plus 1 mm and intentionally allows the shaft exit. Seat, blind shaft and inner-ring tools still require full containment and floor checks. Every tool participates in pairwise batch overlap checks before any cut. Unknown bearing inner-ring dimensions are not inferred from the manual relief diameter.

## Validation status

Version 0.1.8 prefills the inner-ring diameter from Bearing bore, follows bore edits until manual override, and uses an explicit pending state for that bore-equal value. Pending geometry skips the ineffective additional relief cut while retaining seat/shaft preview and creation, reports that state in the dialog and stores pending/applied flags. Actual relief keeps its drawing-based diameter limits. Face inputChanged transfers selection focus using SelectionCommandInput.hasFocus; validateInputs still performs no UI writes. The owner reported no observed errors in a general 0.1.8 trial on 2026-11-03; the exact acceptance cases and Fusion build were not supplied.

The 0.1.6 owner report shows a Through All preview without a shaft opening. In 0.1.7, the ThroughAllExtentDefinition's own isPositiveDirection property is explicitly set to agree with setOneSideExtent. The property was checked against the installed Autodesk Python SDK. Returned features are checked for healthy status, and every cut must reduce target-body volume. A failed feature is deleted inside the extrusion helper before the batch cleanup handles previously created geometry. These checks prevent a warning/no-op extrusion from being reported as a valid preview. The owner confirmed shaft opening and inner-ring relief working in 0.1.7.

In 0.1.4, validateInputs only sets areInputsValid; it no longer writes the status textbox or rechecks placement against temporary preview topology. Status updates run from inputChanged/preview/execute and skip unchanged text. Relevant edits and preview retries clear old errors; real placement/containment/overlap checks remain in the geometry path. This was insufficient on its own: the later 0.1.5 construction-order change resolved the reported profile failure and was confirmed by the owner.

83 automated tests pass, covering pure contour properties, parameter validation/conversion, menu registration, dialog callbacks, cleanup/error paths and snapshots. Tests use an isolated API substitute for Fusion calls. Python/API member checks were also performed against the installed SDK definitions.

The owner confirmed menu launch, version label, Solid > Create placement and working preview/creation in 0.1.5. Shaft/relief operation was subsequently confirmed in 0.1.7, and the owner reported no observed errors in the 0.1.8 trial. Read-only UI inspection found a separate installed AddIns copy rather than the edited repository source. No installed files or user model were changed. macOS remains untested.

## Next proof

The owner confirmed library use and editing existing seats, including batches, in the 0.3.0 trial on 2026-11-04. New screenshots record the dialogs and a valid three-position preview. Run the [0.4.0 preview/wall checks](PREVIEW_AND_WALLS.md#acceptance-in-fusion-pending), the remaining [manual geometry acceptance checks](INSTALLATION.md), and detailed catalog/profile/save-reopen/cancel/undo cases. The general owner report does not close every acceptance case or prove the new 0.4.0 behavior.

## Preview diagnostics API choices in 0.4.0

Markers use one dialog-owned [custom graphics group](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_CustomGraphicsGroups_add.htm), packed world-space [coordinates in centimetres](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_CustomGraphicsCoordinates_create.htm), and independent [line segments](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_CustomGraphicsGroup_addLines.htm). Solid colors indicate error/warning/other candidates; [show-through](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_CustomGraphicsShowThroughColorEffect_create.htm) keeps them visible through the body. Lines are explicitly [nonselectable](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_CustomGraphicsEntity_isSelectable.htm). Cleanup calls [deleteMe](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_CustomGraphicsGroup_deleteMe.htm), checks its result, and retains failed ownership for retry. Validation callbacks do not write controls or create graphics.

Advisory margins use [TemporaryBRepManager.createCylinderOrCone](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_TemporaryBRepManager_createCylinderOrCone.htm) and the existing temporary containment/difference checks. Probes do not create document features. They enclose and enlarge each finite cutting region and test nearby proposed envelopes; failures warn without weakening strict cut validation. Through All shafts are excluded from wall probes. See [probe limits and acceptance](PREVIEW_AND_WALLS.md). These API choices were checked against official Autodesk documentation; native rendering and warning behavior remain pending.

## Official references

The 0.3.0 catalog/profile controls use the existing tabs and command events. Text editors use [CommandInputs.addStringValueInput](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_CommandInputs_addStringValueInput.htm) and writable [StringValueCommandInput.value](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_StringValueCommandInput_value.htm). Search refreshes use [ListItems.clear/add](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_ListItems.htm). Profile dimensions use mm inputs; factors use unitless [value inputs](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_CommandInputs_addValueInput.htm). Model validation and local JSON storage are separate from Fusion. Control writes occur in construction/inputChanged, never validateInputs. The owner confirmed library use; detailed profile/import/export cases still need recorded acceptance.

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

## Chamfer and edit API choices in 0.2.0

The native chamfer uses ChamferFeatures.createInput2 and addEqualDistanceChamferEdgeSet with explicit mm units and tangent-chain expansion disabled. Candidate edges come only from the seat cut side faces and must lie on the original placement plane at both curve endpoints and midpoint. Warning/error features, multiple resulting bodies and no material removal are rejected. The full seat depth remains unchanged. Chamfer is off by default; 0.2-0.6 mm are trial sizes, not guaranteed feasible for every contour.

Before any cut, an enclosing cylinder with diameter contact + 2 * (radial relief + chamfer) and depth chamfer participates in containment and cross-seat overlap checks. It is deliberately conservative: it can reject feasible close-to-edge or close-to-seat placements. Its validation extrusion and sketch are removed rather than retained as final cuts. Fusion's chamfer kernel checks the actual resulting contour; failures reject the whole batch.

Editing uses TimelineObject.index, parentGroup and writable isSuppressed with Timeline.count/markerPosition to guard the last complete batch. Sketches remain available while old cuts are suppressed. See PERSISTENCE_PROTOTYPE.md for transaction and legacy limitations. API members were checked against the installed Autodesk SDK definitions and current official references; this is not live geometry acceptance.

- [Equal-distance chamfer API sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/EqualDistanceChamferFeature_Sample.htm)
- [Extrusion side faces](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_ExtrudeFeature_sideFaces.htm)
- [Timeline objects and suppression](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_TimelineObject.htm)
