# API notes and validation

Reviewed against official Autodesk Fusion API documentation on 2026-11-03.

## Foundation decisions

- Maintain the current version in `version.py`; plugin displays import `VERSION`. Run `python tools/sync_version.py` to copy it to the manifest's JSON version and README current-version header; use `--check` to detect drift without writing files.

- Preserve the owner's Python template: `run` / `stop`, the command registry, and the supplied `fusionAddInUtils` event utilities. Keep the Autodesk notices in the bundled utility sources.
- Use a single command in `FusionSolidEnvironment` / `SolidCreatePanel`, as requested by the owner and documented in Autodesk's UI examples. Remove legacy controls from `SolidScriptsAddinsPanel`. Fail with a visible error if the panel is unavailable.
- Use `CommandInputs.addTabCommandInput` and each tab's `children` collection for the three tabs.
- Set `Command.isOKButtonVisible = False`: Autodesk documents that the remaining Cancel button becomes Close. The foundation creates no model changes.
- Retain handler references for command definitions and open dialogs. Release dialog references on destroy, remove command controls and definitions on stop, and clear remaining global utility handlers in a finally block.
- Package a same-name manifest, Python entry point and folder, with version 0.1.0. Preserve the template's product identifier `Fusion`.
- Use SVG toolbar icons with standard 16x16/32x32 names, plus PNG resources. About uses a 128x128 PNG because `addImageCommandInput` explicitly supports PNG and displays it at its native size.
- Project artwork is copied into the self-contained add-in folder. The About PNG and fallback command PNGs reproduce the logo's circles and five contact lands; the dedicated toolbar SVGs now reproduce `images/logo.svg` with inline paths and matching PNG artwork. Explicit high-DPI PNG names are included.

## Verification status

Static checks passed for Python source parsing, manifest/version alignment, resource existence and PNG signatures. Isolated lifecycle tests cover repeated registration, command cleanup, missing-panel handling, dialog structure and handler release.

The owner confirmed command launch under Utilities on Windows. The command has since moved to Solid > Create and its toolbar resources have changed; those changes and the remaining live acceptance checks are pending. The earlier Computer Use app approval timed out before window inspection. No automated Fusion UI actions or model changes were performed. macOS has not been tested.

## Later milestones

Selection filters, unit conversion, geometry previews, editable features, placement persistence and assembly transforms are deliberately deferred to the 0.2.0 API prototype or the corresponding later milestone. No supported API strategy for editable seat geometry is claimed by the foundation.

## Official references

- [Python add-in template](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/PythonTemplate_UM.htm)
- [Creating scripts and add-ins; manifest](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/WritingDebugging_UM.htm)
- [Command inputs sample](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CommandInputsSample_Sample.htm)
- [Close-only dialog](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Command_isOKButtonVisible.htm)
- [Image input and PNG format](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_CommandInputs_addImageCommandInput.htm)
- [Toolbar customization and icon resources](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/UserInterface_UM.htm)
- [Events and Python handler lifetime](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Events_UM.htm)
