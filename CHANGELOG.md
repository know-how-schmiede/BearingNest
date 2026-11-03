# Changelog

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
