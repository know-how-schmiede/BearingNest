# BearingNest

![BearingNest banner](images/banner.svg)

Version: **0.1.7** · Status: multi-position prototype with optional shaft opening and inner-ring relief; shaft direction correction awaiting live confirmation.

BearingNest creates print-oriented ball bearing seat contours with rounded reliefs and an odd number of contact lands.

## Available in this prototype

![Confirmed BearingNest 0.1.5 seat preview in Fusion](images/screenshots/03-11-2026_13-17-07.png)

The owner confirmed preview and creation working in 0.1.5. See [all four screenshots and their version-specific captions](doku/SCREENSHOTS.md).

- `BearingNest <VERSION>` under Design > Solid > Create, with three English tabs: **Bearing Seat**, **Settings**, **About**.
- One planar face and multiple sketch points, vertices or circular edge centers as seat positions, with shared settings.
- Manual bearing outside diameter/width, diameter and axial corrections, 3/5/7/9 lands, contact angle, rotation, radial relief depth and transition radius.
- Shared construction of [confirmed contour A](doku/CONTOUR_PROPOSAL.md), opt-in cut preview and a **Create Seats** action.
- Checks of every complete solid cutting tool against the selected body, remaining floor and all other proposed seats before the first cut. An invalid position rejects the entire batch.
- Optional shaft opening: Off, Through All or face-referenced Blind depth; positive allowance added to the manual bearing bore.
- Optional manual inner-ring relief starting at the seat floor, with its own diameter and depth.
- A versioned snapshot per seat with its direct-cut and clearance references. Validation tool extrusions are removed before cutting.
- Contour sketches hidden after cutting, with profiles kept enabled for feature calculation; successful creation also hides profile fills on selected placement sketches while preserving points, curves and sketch visibility.

The prototype supports a single solid body in the root component of a parametric design. Chamfer, catalog, print profile management, thin-wall warnings and reopening/editing seats are still pending. The 0.2.0 milestone remains incomplete.

## Install and try

Use the complete [BearingNest add-in folder](Fusion-Add-In/BearingNest). If Fusion loads a copy from its AddIns directory, update that entire copy before restarting the add-in. Restarting alone does not copy repository changes.

Follow the [installation and test guide](doku/INSTALLATION.md), including the [new clearance tests](doku/SHAFT_AND_RELIEF.md), on a disposable design. Preview and creation were confirmed in 0.1.5 after fixing premature profile suppression. The owner reported a missing Through All shaft in 0.1.6. Version 0.1.7 explicitly sets its direction and rejects warning/no-op cuts; live confirmation is pending. Inner-ring relief requires a nonzero drawing-based manual diameter.

Target environments are Autodesk Fusion on Windows and macOS with Fusion's bundled Python. No third-party Python packages are required. The owner confirmed command launch and Solid > Create placement on Windows in an earlier version. The new clearance operations and macOS remain unverified.

## Version maintenance

The only manually maintained current release version is [version.py](Fusion-Add-In/BearingNest/version.py). After changing it, run `python tools/sync_version.py` to update the Fusion manifest and this README header. Check with `python tools/sync_version.py --check`. Plugin displays import the same constant. Historical milestone and changelog versions stay unchanged.

## Project documents

- [Agent and implementation instructions](doku/AGENTS.md)
- [Functional specification](doku/SPECIFICATION.md)
- [Roadmap](doku/ROADMAP.md)
- [Changelog](CHANGELOG.md)
- [Contour A](doku/CONTOUR_PROPOSAL.md)
- [Screenshots of the confirmed 0.1.5 baseline](doku/SCREENSHOTS.md)
- [Shaft opening and inner-ring relief](doku/SHAFT_AND_RELIEF.md)
- [Persistence and remaining edit proof](doku/PERSISTENCE_PROTOTYPE.md)
- [API notes and verification status](doku/API_NOTES.md)
- Visual assets: [logo](images/logo.svg), [banner](images/banner.svg), [bearing seat icon](images/bearing-seat.svg)

The owner's Python template supplies the run/stop entry points, command registry and Autodesk event utilities. Palette examples remain inactive.

Product and documentation language is English. German localization is planned near completion.

Licensed under the [MIT License](LICENSE). Bundled Autodesk utilities retain their [original notices](THIRD_PARTY_NOTICES.md). Manual example dimensions are not manufacturer-verified catalog records.
