# Changelog

## 0.4.2 - 2026-11-05

- Record the owner's successful automatic German selection in German Fusion.
- Remove the introductory version/workflow block and lower shaft-depth summary from Bearing Seat. Place catalog search/selection directly below the create/edit selector. Move profile selection, Auto switches and reset to Settings; remove profile summary/guidance blocks. Retain version information under About and in the command title.
- Default the new-seat dialog's lead-in chamfer to 0.4 mm; saved seats retain their own values.
- Add a bearing-name field and click button below preview status. Save a new custom catalog entry containing bearing dimensions, all current seat parameters, profile snapshot and Auto flags. Selecting that entry restores its preset. Save immediately to local settings, independently of geometry Apply/Cancel; never overwrite an existing entry implicitly.
- Validate optional presets during catalog loading/import and before saving; dimension-only legacy entries remain supported.

Validation: 134 automated tests pass, including layout order, default chamfer, named preset round trip, missing-name rejection and storage failure preservation. Version synchronization passes. Native Fusion layout/button and restored-preset acceptance remain pending.

## 0.4.1 - 2026-11-05

- Bring German UI localization forward at the owner's request. Translate all centralized dialog/help/status strings, parameter and metadata labels, advisory wall warnings and shaft-mode choices. Follow Fusion's user-language preference on add-in start; other languages fall back to English.
- Keep command/input IDs, units, expressions, stored shaft modes and user library/profile content language independent. Restore saved shaft modes using translated display labels.
- Record the owner's report that 0.4.0 runs. This does not establish every detailed acceptance case.
- Technical geometry/storage exception details and bundled profile names remain English. Native German UI layout and edit/preview acceptance remain pending.

Validation: 132 automated tests pass, including German key/format coverage, field/unit preservation, locale fallback and shaft-mode round trips. Version synchronization passes. No native Fusion run was available for this change.

## 0.4.0 - 2026-11-04

- Record the owner's confirmation that the 0.3.0 library and editing existing seats work, including editing multiple seats together. Embed the three new 0.3.0 screenshots and the earlier 0.1.7 clearance screenshot with version-specific captions. Detailed lifecycle/profile/platform cases remain separate.
- Enable Preview by default at the owner's request; retain the ability to switch it off and always rebuild on execute.
- Collect independent placement/containment errors and conflicting pairs before cutting. Show approximate red invalid-position markers, blue other-position markers in rejected batches and selection-order textual reasons. Reject the whole batch without committing a valid subset.
- Add profile-based advisory wall/floor/inter-seat margin probes and amber markers. Temporary enclosing cylinders are conservative and do not measure exact minimum thickness. Intentional Through All exits and lateral through-shaft walls are excluded from wall probes. Advisory failures warn without blocking valid cuts.
- Own transient graphics per dialog and remove them on changes, Preview off, execute, destroy/cancel and stop; retain failed-cleanup ownership for retry. Text remains authoritative if rendering is unavailable.
- Synchronize version, documentation and acceptance procedures. New native graphics, warning behavior and invalid-batch/lifecycle acceptance remain pending.

Validation: 128 automated tests pass. Checks cover batch rejection/cleanup, conservative probes, units and depth references, marker geometry/colors/ownership and preview lifecycle. The owner-tested 0.3.0 screenshots do not establish 0.4.0 behavior.

## 0.3.0 - 2026-11-04

- Add searchable 623/624/625/608 size aliases with principal dimensions verified against the SKF NILOS-Rings bearing table. Unknown ring geometry stays null; RC/MR candidates remain pending verification.
- Add custom bearing metadata, drawing/source fields, optional purchasing URLs, stable custom identities and manual dimension overrides. Seed aliases remain separate from product-specific records.
- Add named nozzle/layer/factor profiles, per-field Auto/Manual flags and reset to suggestions. Switching profiles preserves manual values and independent fit corrections; infeasible geometry remains an error.
- Add validated schema-1 local JSON settings with atomic replacement, custom/profile save/delete and explicit import/export. Corrupt/future-schema files are preserved and block settings writes. Library actions save immediately, separately from geometry Apply/Cancel.
- Persist effective bearing dimensions, original catalog dimensions, source/profile copies and auto flags per seat. Reopening retains historical values; legacy derived fields default to Manual. Guard delayed programmatic selector events from overwriting restored values.
- Synchronize the current release version and document the new workflows and remaining live proof. The owner requested proceeding with catalog/profile development before the separate 0.2.0 acceptance gate was closed.

Validation: 108 automated tests pass, including API-substitute and local-file checks for catalog/profile validation, overrides/reset, storage failure preservation, import/export, historical snapshots and metadata forwarding. Native Fusion UI/save-reopen and Windows/macOS acceptance remain pending; the stored wall threshold does not implement wall detection.

## 0.2.0 - 2026-11-03

- Record the owner's 0.1.8 trial: no observed errors. This confirms the tested baseline without claiming every platform/lifecycle acceptance case was exercised.
- Add an optional native equal-distance 45-degree lead-in chamfer (0 = off), with positive remaining seat depth, rim-only edge selection, feature health and material-removal checks.
- Include a conservative full-circle chamfer envelope in batch containment/overlap preflight before any cuts. Close placements may be rejected even where the exact chamfer would fit.
- Discover saved seats in a Create or edit seats list, refill stored parameters and retain manual relief overrides. New snapshots store batch identities and the relief auto/manual flag; old schema-1 records remain readable with chamfer disabled.
- Rebuild the last complete batch with shared settings inside command transactions. Keep stable seat IDs, bearing/profile metadata and updated feature references. Missing/ambiguous references, later timeline features and groups block this initial edit strategy. Legacy multi-seat creations without batch identities may require recreation.
- Suppress original cuts during rebuild, restore them on failed previews, and delete originals only after successful execute creation. Successful previews rely on Fusion's command rollback; execute errors abort the transaction.
- Update documentation, manifest, menu and README to 0.2.0.

Validation: automated substitute checks cover chamfer rim selection/preflight, snapshot identity, discovery, legacy defaults, failed-preview restoration and edit guards. Native Fusion chamfer/edit, save/reopen, cancellation and undo/redo acceptance is pending; the 0.2.0 roadmap milestone is not yet live-proven.

## 0.1.8 - 2026-11-03

- Prefill Inner-ring relief diameter from Bearing bore, follow bore changes until a manual override, and preserve manually entered diameters.
- Treat the bore-equal value as a pending preset: preview/create the seat and shaft without an ineffective extra relief cut, show an explicit status message and store pending/applied state in the snapshot. Actual relief retains the validated drawing-based diameter limits.
- Move selection focus from the chosen face to Seat positions without stealing focus on parameter edits.
- Synchronize version.py, manifest, menu and README to 0.1.8.

Validation: 66 automated tests pass, including preset updates, manual override preservation, delayed input events, pending-state geometry and selection focus. The owner confirmed shaft opening and inner-ring relief in 0.1.7 and subsequently reported no observed errors in the 0.1.8 trial on 2026-11-03.

## 0.1.7 - 2026-11-03

- Explicitly set ThroughAllExtentDefinition.isPositiveDirection as well as the one-sided extent direction, using the profile sketch normal.
- Reject warning/error extrusions and cuts with no measurable material removal. Remove a failed feature before propagating the error so previews cannot report a no-op shaft as valid and the whole batch can roll back.
- Replace the generic inner-ring validation message with the current diameter and actual shaft/contact limits. A zero manual diameter remains invalid; no bearing dimension is fabricated.
- Synchronize version.py, manifest, menu and README to 0.1.7.

Validation: 59 automated tests pass, including both through-all directions, no-op/warning rejection, shaft-failure rollback and the reported 8.5/21.9 mm inner-ring bounds. The owner reported the missing shaft in 0.1.6; the 0.1.7 fix still needs live confirmation.

## 0.1.6 - 2026-11-03

- Embed all four owner-supplied screenshots in documentation, labelled as the confirmed 0.1.5 baseline; add a preview image to the README.
- Add optional Off / Through All / Blind shaft-opening modes with manual bore and positive diameter allowance. Blind depth is referenced to the selected face.
- Add optional manual inner-ring clearance diameter/depth, starting at the seat floor. Do not infer unknown bearing dimensions or manufacturer-safe support limits.
- Preflight clearance tools with the whole batch, check pairwise envelopes, remove validation extrusions before cutting, and persist clearance modes and feature references.
- Keep feature-driving profiles enabled, scope every cut to the target body, and roll back the whole batch if a clearance operation fails.
- Synchronize version.py, manifest, menu and README to 0.1.6. Chamfer and reopening/editing remain pending.

Validation: 54 automated tests pass, including signed start offsets, native through-all extents, independent depth references and clearance failure cleanup. The owner confirmed 0.1.5 preview/creation; 0.1.6 clearance operations still need live verification.

## 0.1.5 - 2026-11-03

- Address the concrete 0.1.4 preview error: Position 1 could not produce exactly one closed sketch profile.
- Keep generated contour sketches visible with profiles enabled while constructing and consuming their profiles, matching the working 0.1.2 construction order. Hide sketches only after their final cuts; retain profile calculation for feature-driven recomputation.
- Include the observed profile count in any remaining profile error.
- Replace constant-count test profiles with a state-dependent regression substitute and verify that both validation and cut extrusions can access the profile.
- Synchronize version.py, manifest, menu and README to 0.1.5. The 0.1.4 validation-only change was insufficient; this fixes the earlier profile suppression regression.

Validation: 43 automated tests pass. The updated construction order still needs live Fusion confirmation.

## 0.1.4 - 2026-11-03

- Make validateInputs read-only with respect to command inputs: it only sets areInputsValid and no longer rewrites the status textbox while Fusion is validating the dialog.
- Update status text from inputChanged and preview/execute callbacks, skipping identical text to avoid unnecessary input invalidation.
- Keep basic dialog validation independent of face topology temporarily changed by preview; full placement and batch validation still run before preview/creation.
- Clear stale preview errors before retrying and after relevant input changes. Keep actual current preview errors blocking creation.
- Synchronize the central version, manifest, menu and README to 0.1.4.

Validation: 42 automated tests pass, including read-only validation, error recovery and preview retries. The reported disabled button was observed in 0.1.3; the 0.1.4 change has not yet been live-verified.

## 0.1.3 - 2026-11-03

- Allow multiple point, vertex and circular-edge-center selections on one face with shared parameters and a displayed position count.
- Resolve all positions, reject duplicate centers, and validate every contour tool and pairwise overlap before the first cut. Any failure rejects the entire batch, including later cut or snapshot failures.
- Replace retained tool/combine geometry with direct cut extrusions scoped to the selected body; delete hidden validation tools before cutting.
- Hide generated sketch profile fills. Successful creation also disables profile fills on selected placement sketches while retaining their points, curves and visibility. Restore source display flags on failed batches; preview does not alter them.
- Address possible sources of the triangular surface artifacts reported for 0.1.2. The screenshot does not establish the exact cause; the new display behavior still needs live confirmation. Existing seats are not rebuilt automatically.
- Synchronize version.py, manifest, menu label and README to 0.1.3; expand installation and regression instructions.

Validation: 38 automated tests pass using an API substitute. The owner confirmed single-seat creation in 0.1.2; new batch/display changes and macOS remain unverified.

## 0.1.2 - 2026-11-03

- Add one-face/one-position selection and manual bearing/fit/contour inputs in the Bearing Seat tab.
- Share contour A geometry between the add-in and documentation renderer; convert mm/degrees explicitly at the Fusion boundary.
- Add an opt-in preview and Create Seat action using a contour sketch, solid tool extrusion and combine cut.
- Check the complete tool for containment against the selected body and verify remaining floor material before cutting.
- Save a schema-versioned snapshot on successful creation. Abort execute transactions and remove generated features on failures; never persist a preview snapshot.
- Restrict the prototype to parametric root-component solid bodies. Shaft opening, inner-ring relief, chamfer, multi-placement and editing remain pending.
- Update the version source, manifest, README and geometry acceptance instructions.

Validation: 29 automated tests pass, plus source/API checks. Tests substitute the Fusion API; no live geometry, cancellation or undo acceptance is claimed. Inspection found a separate installed AddIns copy, which was not changed.

## 0.1.1 - 2026-11-03

- Display the current release version after the BearingNest command name; synchronize the manifest and README.
- Record owner confirmation of the Solid > Create location and complete contour A proposal.
- Add a prototype snapshot codec with schema versioning, isolated bearing/profile data and stable identities across parameter revisions.
- Add a Fusion attribute adapter for storing/updating one record per feature, discovery and missing/ambiguous reference reporting.
- Keep storage separate from the UI until geometry creation and editing are proven in Fusion; it does not yet create or reopen seats.

Validation: 15 automated tests pass. Menu-label changes and persistence have not been live-tested in Fusion.

## 0.1.0 — 2026-11-03

- Moved the command to Solid > Create, added legacy toolbar cleanup and unified toolbar artwork in a dedicated resource folder. Live verification of these changes is pending.
- Prepared a dimensioned, mathematically tangent contour proposal for review before the 0.2.0 geometry implementation.
- Centralized the current version in `version.py`; plugin displays import it, and `tools/sync_version.py` synchronizes the manifest and README version header.
- Adapted the owner's Python add-in template for the BearingNest foundation.
- Registered one BearingNest command; disabled registration of sample palettes.
- Added Bearing Seat, Settings and About tabs with centralized English strings.
- Integrated project artwork into the add-in icon, command resources and About tab.
- Added manifest version 0.1.0 and included the previously ignored manifest and template utilities in the source package.
- Added repeatable command registration, toolbar cleanup and handler cleanup.
- Documented installation, target environments, API references and outstanding live checks.

Validation: Python syntax, manifest/version consistency, packaged resources and isolated lifecycle tests are checked locally. Live Fusion testing is pending. This version does not implement geometry, preview, persistent editing, a catalog or stored print profiles.
