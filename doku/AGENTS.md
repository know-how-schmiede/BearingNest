# BearingNest — project instructions

## Scope and starting point

- Start at version 0.1.0. Do not imply that specification assets constitute a working release.
- Read [the functional specification](SPECIFICATION.md) and [the roadmap](ROADMAP.md) before implementation.
- Inspect the owner's `/Fusion-Add-In` template and its instructions when it arrives. Preserve its lifecycle and conventions; do not replace it with an unrelated scaffold.
- Use the current official Autodesk Fusion API documentation to verify API choices, selection filters, preview lifecycle, editable feature support, units and resource formats. Do not invent API capabilities.
- Implement in the template's language. If it is Python, keep pure geometry/validation and persistence separate from Fusion API calls.

## Product rules

- Exactly three initial dialog tabs: **Bearing Seat**, **Settings**, **About**.
- Register BearingNest in Design > Solid > Create (`FusionSolidEnvironment` / `SolidCreatePanel`), promoted to the toolbar. Do not register it under Utilities > Add-Ins. Remove any legacy BearingNest control there during migration and cleanup.
- Use the BearingNest logo consistently for toolbar SVG/PNG resources. Keep toolbar resources in the dedicated `resources/toolbar` folder; the About image remains a PNG in `resources`.
- Use [confirmed contour A](CONTOUR_PROPOSAL.md) for the geometry prototype: circular inner/outer fillets joined by a radial wall, derived transition width and full axial seat depth below the lead-in. The owner confirmed this construction; do not ask for confirmation again.
- Develop the UI, identifiers, messages, comments and project documentation in English.
- Introduce localization near completion. English is the source locale; German is a translation. Keep UI strings centralized now, without implementing the full translation system prematurely.
- Keep bearing dimensions, manufacturing corrections and print-derived defaults separate.
- For shaft openings, use d plus a positive diameter allowance; Blind depth is measured from the selected face. Inner-ring relief starts at the seat floor and requires a manual, drawing-based diameter when bearing data is unknown. Preserve unknown bearing values and never claim safe outer-ring support from diameter inequalities alone.
- Prefill the inner-ring clearance diameter from Bearing bore and follow bore edits until a manual override. The bore-equal preset is an explicit pending state: allow the seat/shaft preview and creation, display that no additional relief is cut, and store pending/applied state in snapshots. Actual relief still requires a drawing-based diameter above the shaft opening and below the contact diameter. Never fabricate an inner-ring bearing dimension.
- In inputChanged, transfer selection focus to Seat positions after one face is selected; do not steal focus on unrelated parameter edits or focus an invisible selector. Keep preset/focus writes outside validateInputs.
- Include optional shaft/relief envelopes in batch preflight before any cut. Only a deliberate Through All shaft exit is exempt from closed-tool containment; final cuts must retain explicit participantBodies.
- Set ThroughAllExtentDefinition.isPositiveDirection explicitly in addition to setOneSideExtent's direction. Check feature health and measurable material removal before accepting any cut. A returned feature or body count alone does not prove a successful cut; remove failed newly created features and reject the whole batch.
- Keep owner-supplied screenshots embedded in the documentation with accurate version captions. The images under images/screenshots currently document the confirmed 0.1.5 baseline; do not present them as proof of newer clearance features.
- Store a snapshot of each seat's values and bearing data with a schema version. Library/profile edits must not silently alter existing seats.
- Support reopening and editing seats created by BearingNest. Prototype the persistence and edit strategy before building the complete geometry engine; use supported Fusion capabilities and document limitations.
- Convert millimetres and degrees explicitly at the Fusion API boundary; do not assume API internal units.
- Never leave permanent geometry behind after cancelling a preview. Clean up event handlers on stop.
- Keep validateInputs free of command-input writes and model changes: only set areInputsValid. Update status text from inputChanged/preview/execute, avoid identical repeated writes, and do not validate placement topology against already-modified preview geometry. Clear stale preview errors on relevant edits and successful retries.
- For multiple seats, validate all positions before committing. Reject an invalid batch without partial permanent cuts.
- The current prototype supports batches on one planar face of a parametric root-component body. Prepare all contours and validate containment and pairwise overlap before the first cut. Delete hidden validation extrusions before creating direct cut extrusions restricted to the target body; do not retain coplanar tool bodies. Do not equate isolated API-substitute tests with live Fusion preview/undo verification.
- Keep generated contour sketches and their profile calculation enabled while building and consuming their profiles. Hide generated sketches with isVisible=False only after their final cuts; do not disable areProfilesShown on these feature-driving sketches. On successful creation, disable only profile fills of selected placement sketches, leaving their points, curves and visibility intact; restore original fills if the batch fails. Preview must not alter source sketch profile-display preferences.
- Thin walls produce warnings only. Unintended breakout and conflicting seats are errors; deliberate shaft through-holes are allowed.

## Validation and delivery

- Include the current version after the plugin command name in the menu (`BearingNest <VERSION>`). Keep command IDs stable across version updates. The owner confirmed the Solid > Create menu position.

- Use `Fusion-Add-In/BearingNest/version.py` and its `VERSION` constant as the only manually maintained current release version. Import it directly in plugin code; do not define a separate version in `config.py` or UI strings.
- After changing `version.py`, run `python tools/sync_version.py` from the repository root. This updates the manifest's literal JSON version and the README current-version header. Fusion cannot import Python values from its manifest.
- Before delivery, run `python tools/sync_version.py --check` and the automated tests. Fix version drift before packaging. Keep historical changelog entries and roadmap milestone versions unchanged; document release behavior separately.

- Test geometry math, unit conversion, correction signs, profile overrides, persistence migrations and invalid placement behavior where meaningful.
- Verify actual commands, previews, cancellation, edits and feature creation in Fusion. Clearly distinguish automated checks from manual Fusion checks.
- Verify source dimensions for the seed bearing catalog. Unknown inner-ring dimensions stay unknown; never fabricate them.
- Keep the README, roadmap, version and changelog aligned with actual implemented behavior.
- Do not publish, upload or create the owner's GitHub repository. Prepare local files for the owner to copy.
