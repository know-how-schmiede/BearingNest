# BearingNest

![BearingNest banner](images/banner.svg)

Version: **0.1.5** · Status: multi-position prototype; profile-construction fix awaiting live verification.

BearingNest creates print-oriented ball bearing seat contours with rounded reliefs and an odd number of contact lands.

## Available in this prototype

- `BearingNest <VERSION>` under Design > Solid > Create, with three English tabs: **Bearing Seat**, **Settings**, **About**.
- One planar face and multiple sketch points, vertices or circular edge centers as seat positions, with shared settings.
- Manual bearing outside diameter/width, diameter and axial corrections, 3/5/7/9 lands, contact angle, rotation, radial relief depth and transition radius.
- Shared construction of [confirmed contour A](doku/CONTOUR_PROPOSAL.md), opt-in cut preview and a **Create Seats** action.
- Checks of every complete solid cutting tool against the selected body, remaining floor and all other proposed seats before the first cut. An invalid position rejects the entire batch.
- A versioned snapshot on each direct cut extrusion. Validation tool extrusions are removed before cutting.
- Contour sketches hidden after cutting, with profiles kept enabled for feature calculation; successful creation also hides profile fills on selected placement sketches while preserving points, curves and sketch visibility.

The prototype supports a single solid body in the root component of a parametric design. It does not yet provide a shaft opening, inner-ring relief, chamfer, catalog, print profile management, thin-wall warnings or reopening/editing seats. The 0.2.0 milestone remains incomplete.

## Install and try

Use the complete [BearingNest add-in folder](Fusion-Add-In/BearingNest). If Fusion loads a copy from its AddIns directory, update that entire copy before restarting the add-in. Restarting alone does not copy repository changes.

Follow the [installation and test guide](doku/INSTALLATION.md). First test on a disposable design. The owner confirmed single-seat creation in 0.1.2 and reported triangular surface artifacts. The 0.1.3 batch and display changes have automated tests using an API substitute; their live verification is pending. Version 0.1.4 made dialog validation read-only but did not resolve the reported error. Version 0.1.5 keeps sketches/profiles enabled until the final cut and hides sketches afterwards; live confirmation remains pending.

Target environments are Autodesk Fusion on Windows and macOS with Fusion's bundled Python. No third-party Python packages are required. The owner confirmed command launch and Solid > Create placement on Windows in an earlier version. The new batch/display behavior and macOS remain unverified.

## Version maintenance

The only manually maintained current release version is [version.py](Fusion-Add-In/BearingNest/version.py). After changing it, run `python tools/sync_version.py` to update the Fusion manifest and this README header. Check with `python tools/sync_version.py --check`. Plugin displays import the same constant. Historical milestone and changelog versions stay unchanged.

## Project documents

- [Agent and implementation instructions](doku/AGENTS.md)
- [Functional specification](doku/SPECIFICATION.md)
- [Roadmap](doku/ROADMAP.md)
- [Changelog](CHANGELOG.md)
- [Contour A](doku/CONTOUR_PROPOSAL.md)
- [Persistence and remaining edit proof](doku/PERSISTENCE_PROTOTYPE.md)
- [API notes and verification status](doku/API_NOTES.md)
- Visual assets: [logo](images/logo.svg), [banner](images/banner.svg), [bearing seat icon](images/bearing-seat.svg)

The owner's Python template supplies the run/stop entry points, command registry and Autodesk event utilities. Palette examples remain inactive.

Product and documentation language is English. German localization is planned near completion.

Licensed under the [MIT License](LICENSE). Bundled Autodesk utilities retain their [original notices](THIRD_PARTY_NOTICES.md). Manual example dimensions are not manufacturer-verified catalog records.
