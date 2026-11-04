# BearingNest in Fusion

These owner-supplied screenshots document **0.3.0**, **0.1.7** and the earlier **0.1.5** baseline. On 2026-11-04 the owner confirmed that the library works and existing seats can be edited, including several seats together. This is a live usage report, not a completed test matrix for save/reopen, cancellation, undo/redo, import/export or every profile operation. No screenshot below documents the new 0.4.0 diagnostic markers or wall warnings.

## 0.3.0: catalog selection and three-position preview

![BearingNest 0.3.0 in Fusion with bearing 625 selected and a valid preview for three positions](../images/screenshots/04-11-2026_22-13-22.png)

The active command shows one selected face, three selected positions, catalog size 625 (5 x 16 x 5 mm), five 30-degree lands and Preview enabled. The status reports a valid preview for three seats, a 15.900 mm contact diameter and a 5.000 mm depth. Shaft opening and chamfer are off in this example. Seats on other visible faces were already present; this does not establish a single multi-face batch. The separate owner report confirms editing existing seats and whole batches; the screenshot itself shows **Create new seats**.

## 0.3.0: Bearing Seat tab

![BearingNest 0.3.0 Bearing Seat tab with catalog search, print profile and Auto controls](../images/screenshots/04-11-2026_22-12-10.png)

The complete dialog shows manual bearing values, batch selection, shaft/relief controls, catalog search and the provisional 0.4 mm nozzle / 0.2 mm layer profile. All three derived fields are Auto. Preview is unchecked in this historical 0.3.0 screenshot; **0.4.0 changes the startup default to on**.

## 0.3.0: Settings tab

![BearingNest 0.3.0 Settings tab with custom bearing metadata, named profiles and JSON import/export](../images/screenshots/04-11-2026_22-12-19.png)

The Settings tab contains custom identity, designation, manufacturer/part number, source, notes, optional purchasing URL and an unknown inner-ring diameter represented by 0 in the editor. It also shows print profile factors, local settings actions and JSON import/export. Its wording describes wall warnings as pending in 0.3.0; conservative advisory probes are introduced in 0.4.0. The screenshot shows the controls, not proof that every settings action was exercised.

## 0.1.7: shaft opening and inner-ring relief

![BearingNest 0.1.7 preview with a blind shaft opening and manual inner-ring relief](../images/screenshots/03-11-2026_16-40-17.png)

This earlier screenshot shows a 22 x 7 mm seat, an 8 mm bearing bore, 0.2 mm shaft allowance, a face-referenced 12 mm blind opening, and a manual 12 mm diameter / 0.4 mm deep inner-ring relief. The status reports one valid seat preview. The owner confirmed shaft/relief operation in 0.1.7; this image predates catalog/profile controls and editable batches.

## Historical 0.1.5 baseline

The four images below record the owner-confirmed 2026-11-03 baseline, before shaft/relief, catalog/profile and batch-edit controls.

## Seat preview on a planar inclined face

![BearingNest 0.1.5 showing a valid seat preview on an inclined planar face, with other seats already present](../images/screenshots/03-11-2026_13-17-07.png)

The active preview contains one selected position. The other visible seats were already present; this image alone is not proof of a single multi-face batch.

## Bearing Seat tab

![Bearing Seat tab in version 0.1.5 with Preview enabled and Create Seats available](../images/screenshots/03-11-2026_13-17-24.png)

The example uses a 22 mm outside diameter, 7 mm bearing width, -0.10 mm diameter correction and five 30-degree contact lands. The displayed contact diameter is 21.900 mm and depth is 7.000 mm.

## Settings tab

![Settings tab in version 0.1.5 describing planned library and print profile management](../images/screenshots/03-11-2026_13-17-31.png)

Library and print profile management were planned features in 0.1.5. This historical tab describes their intended role; the 0.3.0 implementation appears above.

## About tab

![About tab in version 0.1.5 with the BearingNest logo, version and parameter conventions](../images/screenshots/03-11-2026_13-17-39.png)

The About tab displays the logo, centrally maintained version and correction-sign guidance. Its limitations describe the historical 0.1.5 implementation.
