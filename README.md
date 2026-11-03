# BearingNest

![BearingNest banner](images/banner.svg)

Version: **0.1.1** · Status: dialog foundation implemented; initial command launch confirmed by the owner; full live verification pending.

BearingNest is a Fusion add-in project for creating 3D-print-oriented ball bearing seats with rounded reliefs and an odd number of contact lands.

## Available in the 0.1 series

- One BearingNest command in the Design workspace, under Solid > Create. The menu label includes the current version from version.py.
- Exactly three English dialog tabs: **Bearing Seat**, **Settings**, **About**.
- Integrated command icons, About logo, version and parameter guidance.
- Template-based command registration and cleanup on stop.

The menu position is confirmed by the owner. The updated version label still needs a live check. An internal snapshot/attribute prototype is covered by isolated tests and is not yet wired to seat creation.

This version provides an informational, Close-only dialog. It does not create geometry, select faces, preview cuts, save settings or edit seats. Geometry and persistent editing start with the 0.2.0 prototype.

## Install and check

Register the complete [BearingNest add-in folder](Fusion-Add-In/BearingNest) in Fusion's Scripts and Add-Ins dialog. Keep its name and contents intact, including the manifest, `lib` and command resources. Follow the [installation and verification guide](doku/INSTALLATION.md).

Target environments are Autodesk Fusion on Windows and macOS, using Fusion's bundled Python runtime. No third-party Python packages are required. Neither platform has completed live verification; no minimum Fusion build is claimed yet.

## Project documents

The current version is maintained in [version.py](Fusion-Add-In/BearingNest/version.py). After changing it, run `python tools/sync_version.py` to update this page's version header and the Fusion manifest. Verify consistency with `python tools/sync_version.py --check`. Plugin version displays import the same constant directly. Historical milestone and changelog versions remain unchanged.

- [Agent and implementation instructions](doku/AGENTS.md)
- [Functional specification](doku/SPECIFICATION.md)
- [Roadmap](doku/ROADMAP.md)
- [Dimensioned contour proposal](doku/CONTOUR_PROPOSAL.md)
- [Persistence prototype and remaining Fusion checks](doku/PERSISTENCE_PROTOTYPE.md)
- [Changelog](CHANGELOG.md)
- [API notes and verification status](doku/API_NOTES.md)
- Visual assets: [logo](images/logo.svg), [banner](images/banner.svg), [bearing seat icon](images/bearing-seat.svg)

The owner's Python template in `Fusion-Add-In` supplies the run/stop entry points, command registry and Autodesk event utilities. Palette examples remain in the source tree for reference and are not registered.

The initial product and documentation language is English. Localization is planned near completion, with English as the source language and German as the first translation.

Licensed under the [MIT License](LICENSE). The bundled Autodesk utilities retain their [original copyright and warranty notices](THIRD_PARTY_NOTICES.md). Bearing data must be manufacturer-verified before catalog release.
