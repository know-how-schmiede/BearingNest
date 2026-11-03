# BearingNest — functional specification

Target starting version: 0.1.0. Requirements below are agreed unless marked **provisional** or **implementation decision**.

## Placement and workflow

Select a planar face and one or more supported points or circle centers on that face. Circle selection supplies a center; bearing dimensions come from the library. Initial multi-placement uses shared settings. Create the seat, concentric shaft opening and inner-ring relief by cutting the selected body. Scope component/assembly transforms explicitly during the API prototype.

## Dialog

1. **Bearing Seat**: face/position selection, searchable bearing library selection, dimensions, land count and width, pattern rotation, diameter correction, axial position, lead-in chamfer, shaft opening, inner-ring relief, preview and resulting effective dimensions.
2. **Settings**: bearing library management and named print profile management. Allow custom bearing entries and manual dimension overrides. Manage nozzle diameter, layer height, relief factors and thin-wall warning threshold. Local JSON import/export is a provisional storage choice; include schema versions and input validation.
3. **About**: logo, version, purpose, concise workflow, parameter/sign explanations, printing guidance, limitations, and project/documentation links once available. Never invent repository URLs.

## Bearing library

Store designation, bore `d`, outside diameter `D`, width `B`, optional inner-ring outside/shoulder diameter, manufacturer, manufacturer part number, source reference, notes and optional purchasing URL (including user-provided short links). Units are mm. Separate size aliases from manufacturer-specific products; do not imply all same-size bearings have identical internal ring geometry.

Seed candidates, subject to manufacturer validation:

| Category | Designation | d | D | B |
|---|---|---:|---:|---:|
| Tamiya/RC | 850 | 5 | 8 | 2.5 |
| Tamiya/RC | 950 | 5 | 9 | 3 |
| Tamiya/RC | 1050 | 5 | 10 | 4 |
| Tamiya/RC | 1150 | 5 | 11 | 4 |
| Tamiya/RC | 1060 | 6 | 10 | 3 |
| Tamiya/RC | 1260 | 6 | 12 | 4 |
| Tamiya/RC | 1280 | 8 | 12 | 3.5 |
| Tamiya/RC | 1510 | 10 | 15 | 4 |
| Maker | 623 | 3 | 10 | 4 |
| Maker | 624 | 4 | 13 | 5 |
| Maker | 625 | 5 | 16 | 5 |
| Maker | 608 | 8 | 22 | 7 |
| Maker | MR83 | 3 | 8 | 3 |
| Maker | MR105 | 5 | 10 | 4 |

1050/MR105 may share a size record. Tamiya names can have width variants: store the complete dimensions in every displayed entry. Flanged bearings and profiled guide rollers are outside the initial geometry scope. Linear bearings are excluded.

Manufacturer drawings may call the inner-ring shoulder diameter `d1`; verify the drawing rather than relying on notation alone. Do not confuse it with bore `d` or shaft abutment `da`. Unknown values require manual entry before automatic inner-ring clearance calculation.

## Seat geometry

- Contact land count: **3, 5, 7, 9**; evenly distributed angularly. Free odd-number entry may follow later.
- Land width modes: fixed angle (presets 20°, 30°, 40°) or fraction of pitch. Pitch = 360° / count; land angle = pitch × fraction. Enforce enough remaining space for relief transitions.
- Contact diameter = `D + correction`. Correction presets in mm: **0, -0.05, -0.10, -0.15, -0.20**. Negative correction tightens the fit; radial interference is half its magnitude.
- Axial correction is measured from the selected face. Zero places the bearing top flush; positive recesses it, negative makes it protrude. Seat depth = `B + axial correction`; reject nonpositive depths.
- User-defined 45° lead-in chamfer; presets **0.2–0.6 mm**, provisional default **0.4 mm**. Size means equal axial/radial legs. Validate against neighboring geometry.
- Rounded reliefs flank the contact lands. Use tangent transitions without sharp sketch corners. Exact curve construction and axial extent must be settled with a dimensioned contour/prototype before geometry is called final; screenshots are intent references, not a complete mathematical definition.
- Wider contact lands generally increase engagement, but the UI must not promise a calculated insertion force.

## Print-derived defaults

| Dimension | Proposed automatic formula |
|---|---|
| Side relief width | 2 × nozzle diameter |
| Radial relief depth | 3 × nozzle diameter |
| Transition radius | 1 × nozzle diameter |
| Inner-ring relief depth | 2 × layer height |

These are provisional starting values for printed trials, not proven universal fits. Show factor and effective mm. Each field has Auto/Manual mode and Reset to suggested value. Manual overrides survive profile changes. Store profiles by name; selecting a profile updates only auto-derived values. Nozzle and layer values must be positive. Validate tangency/radius feasibility rather than silently changing user dimensions.

Layer multiples correspond to actual print layers only when seat axis aligns with print Z. Toolpaths remain the slicer's responsibility; rounded CAD geometry does not guarantee smooth machine motion.

## Shaft opening and inner-ring relief

- Shaft opening diameter = bore `d` + positive user allowance; must exceed `d`.
- Modes: Through All or Blind. Blind depth is measured from the selected face, independently of the axial seat correction. Show this reference in the UI and preview.
- Inner-ring relief starts at seat floor, with independent depth. Suggested diameter = inner-ring outside diameter + 2 × radial clearance; manually overridable. Radial clearance default remains to be calibrated.
- Inner-ring relief diameter must exceed shaft opening diameter. Keep sufficient outer-ring axial support, and avoid unintended contact with seals/shields. Validate using available product drawing data; do not infer a safe support limit solely from `d`, `D`, `B`.
- For blind openings, the final opening must extend deeper than the inner-ring relief if a separate shaft pocket is to exist. Explain inconsistent settings.

## Preview and validation

Show all proposed seats and their approximate dimensions before commit. Invalid positions (outside body, unintended breakout, collision/overlap) are red and accompanied by a textual reason. The user manually changes or removes positions; do not relocate automatically. Invalid positions block batch creation.

Thin remaining walls produce a warning only; allow creation when the complete contour stays within the body. The constructor owns wall thickness suitability. A configurable nozzle-based warning threshold is advisory, with its initial factor still to be calibrated. Detect lateral breakout, insufficient axial depth for seat/relief/blind opening, and overlap between complete cut envelopes. Intentional shaft Through All breakout is permitted.

## Persistence and editing

Persist placement references, effective geometry parameters, auto/manual flags, selected profile snapshot, bearing snapshot, schema version and identifiers needed to locate generated geometry. Reopening must populate the three-tab dialog and support preview/apply/cancel. Detect lost references and report repair requirements. Edits must not duplicate seats or leave failed partial results. Native parameter dependencies and edit strategy are subject to the supported Fusion API prototype.

## Remaining decisions

- Final side-relief curve definition and axial extent, confirmed by the owner or a dimensioned prototype.
- Calibrated profile defaults, minimum useful outer-ring support and radial inner-ring clearance.
- Final manufacturer-verified library records and purchasing links.
- License, publisher identity, actual repository URL and supported Fusion/platform versions.

These do not block project setup; they gate the relevant implementation/release milestone.
