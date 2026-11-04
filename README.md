# BearingNest

![BearingNest banner](images/banner.svg)

Version: **0.3.0** · Status: catalog/profile prototype; owner tested 0.1.8 without observed errors. Geometry/edit and new catalog/profile UI await live Fusion acceptance.

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
- Optional 45-degree lead-in chamfer with equal axial/radial legs; 0 mm disables it. A conservative enclosing-cylinder preflight may reject close placements.
- A versioned snapshot per seat with direct-cut, clearance and chamfer references, stable seat identity and creation-batch identity. Validation tool extrusions are removed before cutting.
- A Create or edit seats list reloads saved batches. The last complete batch can be rebuilt with shared settings; downstream features, timeline groups and missing/ambiguous references block editing.
- Searchable verified seed sizes 623/624/625/608, custom bearing records with sources and optional purchasing URLs, and manual dimension overrides.
- Named print profiles with per-field Auto/Manual settings, reset to suggestions, versioned local JSON storage and validated import/export. Existing seats keep independent bearing/profile snapshots.
- Contour sketches hidden after cutting, with profiles kept enabled for feature calculation; successful creation also hides profile fills on selected placement sketches while preserving points, curves and sketch visibility.

The prototype supports a single solid body in the root component of a parametric design. Further seed sizes, thin-wall warnings and editing with downstream features remain pending. The 0.2.0 geometry/edit proof remains open; the owner requested proceeding with 0.3.0 catalog/profile development. The new dialog and local persistence also require live Fusion acceptance. See the [catalog/profile guide and acceptance procedure](doku/CATALOG_AND_PROFILES.md).

## Install and try

Use the complete [BearingNest add-in folder](Fusion-Add-In/BearingNest). If Fusion loads a copy from its AddIns directory, update that entire copy before restarting the add-in. Restarting alone does not copy repository changes.

Follow the [installation and test guide](doku/INSTALLATION.md), including the [new clearance tests](doku/SHAFT_AND_RELIEF.md), on a disposable design. Preview and creation were confirmed in 0.1.5 after fixing premature profile suppression. The owner reported a missing Through All shaft in 0.1.6. The owner confirmed shaft opening and inner-ring relief working in 0.1.7. The owner reported no observed errors while testing 0.1.8 on 2026-11-03. This is a general trial report, not a completed matrix of every acceptance case. The bore preset previews/creates the seat and shaft without an additional relief cut; a larger drawing-based diameter enables actual relief.

Target environments are Autodesk Fusion on Windows and macOS with Fusion's bundled Python. No third-party Python packages are required. The owner confirmed command launch and Solid > Create placement on Windows in an earlier version. The new 0.2.0 chamfer/edit operations and macOS remain unverified.

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
- [Persistence, batch editing and remaining live proof](doku/PERSISTENCE_PROTOTYPE.md)
- [Bearing catalog, named print profiles and local settings](doku/CATALOG_AND_PROFILES.md)
- [API notes and verification status](doku/API_NOTES.md)
- Visual assets: [logo](images/logo.svg), [banner](images/banner.svg), [bearing seat icon](images/bearing-seat.svg)

The owner's Python template supplies the run/stop entry points, command registry and Autodesk event utilities. Palette examples remain inactive.

Product and documentation language is English. German localization is planned near completion.

Licensed under the [MIT License](LICENSE). Bundled Autodesk utilities retain their [original notices](THIRD_PARTY_NOTICES.md). Manual example dimensions are not manufacturer-verified catalog records.
