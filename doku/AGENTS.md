# BearingNest — project instructions

## Scope and starting point

- Start at version 0.1.0. Do not imply that specification assets constitute a working release.
- Read [the functional specification](SPECIFICATION.md) and [the roadmap](ROADMAP.md) before implementation.
- Inspect the owner's `/Fusion-Add-In` template and its instructions when it arrives. Preserve its lifecycle and conventions; do not replace it with an unrelated scaffold.
- Use the current official Autodesk Fusion API documentation to verify API choices, selection filters, preview lifecycle, editable feature support, units and resource formats. Do not invent API capabilities.
- Implement in the template's language. If it is Python, keep pure geometry/validation and persistence separate from Fusion API calls.

## Product rules

- Exactly three initial dialog tabs: **Bearing Seat**, **Settings**, **About**.
- Develop the UI, identifiers, messages, comments and project documentation in English.
- Introduce localization near completion. English is the source locale; German is a translation. Keep UI strings centralized now, without implementing the full translation system prematurely.
- Keep bearing dimensions, manufacturing corrections and print-derived defaults separate.
- Store a snapshot of each seat's values and bearing data with a schema version. Library/profile edits must not silently alter existing seats.
- Support reopening and editing seats created by BearingNest. Prototype the persistence and edit strategy before building the complete geometry engine; use supported Fusion capabilities and document limitations.
- Convert millimetres and degrees explicitly at the Fusion API boundary; do not assume API internal units.
- Never leave permanent geometry behind after cancelling a preview. Clean up event handlers on stop.
- For multiple seats, validate all positions before committing. Reject an invalid batch without partial permanent cuts.
- Thin walls produce warnings only. Unintended breakout and conflicting seats are errors; deliberate shaft through-holes are allowed.

## Validation and delivery

- Use `Fusion-Add-In/BearingNest/version.py` and its `VERSION` constant as the only manually maintained current release version. Import it directly in plugin code; do not define a separate version in `config.py` or UI strings.
- After changing `version.py`, run `python tools/sync_version.py` from the repository root. This updates the manifest's literal JSON version and the README current-version header. Fusion cannot import Python values from its manifest.
- Before delivery, run `python tools/sync_version.py --check` and the automated tests. Fix version drift before packaging. Keep historical changelog entries and roadmap milestone versions unchanged; document release behavior separately.

- Test geometry math, unit conversion, correction signs, profile overrides, persistence migrations and invalid placement behavior where meaningful.
- Verify actual commands, previews, cancellation, edits and feature creation in Fusion. Clearly distinguish automated checks from manual Fusion checks.
- Verify source dimensions for the seed bearing catalog. Unknown inner-ring dimensions stay unknown; never fabricate them.
- Keep the README, roadmap, version and changelog aligned with actual implemented behavior.
- Do not publish, upload or create the owner's GitHub repository. Prepare local files for the owner to copy.
