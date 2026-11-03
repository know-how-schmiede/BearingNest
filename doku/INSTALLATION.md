# Installation and verification

## Environment

Target: Autodesk Fusion desktop on Windows or macOS with its bundled Python API. The manifest enables both platforms. Windows and macOS live checks are pending; the minimum supported Fusion build will be recorded after validation. The implementation uses only the Python standard library and Fusion's API.

The foundation contains no geometry engine or third-party dependencies. A separate system Python installation is not required to run the add-in.

## Register the add-in

1. Keep the complete `Fusion-Add-In/BearingNest` folder together. The folder, `BearingNest.py` and `BearingNest.manifest` must share the same base name.
2. In Fusion, open **Utilities > Add-Ins > Scripts and Add-Ins**.
3. Add an existing add-in and choose the BearingNest folder (or its manifest if requested by your Fusion dialog).
4. Select BearingNest and run it. Run on Startup is disabled by default; enable it only after checking the add-in.
5. In the Design workspace, open **Solid > Create > BearingNest <VERSION>**, using the current version from version.py. Stop and restart the add-in after updating the source.

Fusion UI labels vary by version and language. See [Autodesk's installation guide](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/How-to-install-an-ADD-IN-and-Script-in-Fusion-360.html).

Do not copy only the main Python file. The manifest, `commands`, `config.py`, `version.py`, `strings.py`, `lib/fusionAddInUtils` and image resources are required. The original palette example folders may remain; they are inactive.

## Manual acceptance checks

The owner confirmed command launch and the Solid > Create menu position. The version suffix and updated toolbar icon still need live verification; the remaining acceptance checks below are pending.

1. Record OS, Fusion build and add-in version. Stop the previous add-in, then start the updated source. Under Solid > Create, exactly one BearingNest command appears, with its icon and no sample palette commands.
2. Open the command: exactly **Bearing Seat**, **Settings**, **About** tabs appear in English. Switch through all three and check that text is legible.
3. In About, confirm the logo is visible and the version matches `VERSION` in `version.py` and the manifest.
4. Confirm there is no creation/OK action; close the dialog. The model and timeline remain unchanged.
5. Reopen and close the dialog several times. Confirm no error dialogs or duplicated UI.
6. Stop the add-in: the BearingNest toolbar command disappears.
7. Start, open, close and stop again. Confirm the same behavior without duplicate commands or handler errors.
8. Repeat on macOS before claiming verified macOS support.

For a safe check, use a disposable design. Geometry, preview cancellation and editing acceptance tests belong to later milestones.

## Stop or remove

Close the BearingNest dialog, then stop the add-in in Scripts and Add-Ins. Disable Run on Startup if enabled. Removing its registration does not require changing a design.

## Local checks

Run `python -m unittest discover -s tests -v` from the repository root with Python 3. The tests use an isolated API substitute to check lifecycle behavior; they do not substitute for Fusion acceptance testing.

Maintain the release version only in `Fusion-Add-In/BearingNest/version.py`. Run `python tools/sync_version.py` after changing it, then `python tools/sync_version.py --check` before packaging. The script writes the required literal JSON value into the manifest and updates the README current-version header. It does not rewrite historical release notes or roadmap milestones.
