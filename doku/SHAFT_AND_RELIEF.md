# Shaft opening and inner-ring relief

Implemented in 0.1.6, with the shaft and relief corrections **confirmed by the owner in 0.1.7**. Version 0.1.8 adds bore-prefill and selection-focus changes awaiting live confirmation. The owner reported that the 0.1.6 Through All preview showed no shaft opening. Version 0.1.7 sets the extent's own direction flag and rejects warning/error or no-material-removal features. See the [0.1.5 screenshots](SCREENSHOTS.md) for the confirmed seat baseline.

## Controls

All selected positions share the same values. Shaft opening defaults to **Off**, preserving the established seat-only workflow.

| Control | Meaning |
|---|---|
| Shaft opening: Off | Create only the rounded seat. |
| Shaft opening: Through All | Cut inward from the selected face through the selected body. The shaft exit is intentional; other bodies are excluded. |
| Shaft opening: Blind | Cut to the specified depth measured from the selected face, independently of axial correction. |
| Bearing bore (manual) | Actual bearing bore d from a drawing. The displayed 8 mm is an editable example, not a verified catalog entry. |
| Shaft diameter allowance | Positive diametral allowance added to d. Shaft opening diameter = d + allowance. |
| Inner-ring relief | Optional circular clearance starting at the seat floor. Requires a shaft opening. |
| Inner-ring relief diameter (manual) | Starts at Bearing bore and follows bore edits until manually changed. This preset permits the seat/shaft preview but adds no separate relief cut. Enter a larger drawing-based diameter to create actual relief. |
| Inner-ring relief depth | Additional depth below the seat floor. |

Only the controls relevant to the selected mode are enabled. Switching the shaft mode to Off deactivates the inner-ring option without applying its retained preference or inactive invalid expressions.

## Example test dimensions

Use a disposable 60 x 60 x 20 mm root-component solid with a top-face center point:

- Bearing outside diameter 22 mm, width 7 mm, diameter correction -0.10 mm, axial correction +0.50 mm.
- Seat floor is 7.50 mm below the selected face.
- Set Shaft opening to Blind, bearing bore 8 mm, allowance 0.20 mm, blind depth 12 mm. The opening diameter is 8.20 mm; blind depth remains 12 mm from the face.
- Enable Inner-ring relief and manually enter diameter 12 mm and depth 0.40 mm. Its bottom is 7.90 mm below the face. These are illustrative geometry-test values; verify support and clearance against the real bearing drawing before printing.

The relief diameter must exceed the shaft opening diameter and remain below the contact diameter; its depth must be positive. These inequalities ensure geometric nesting, not safe manufacturer-specific outer-ring support or seal clearance. Unknown inner-ring outside dimensions remain unknown in the bearing snapshot.

Since 0.1.8, a diameter equal to Bearing bore is an explicit pending preset. Seat and shaft preview/creation stay available, while status text explains that no extra relief is cut. Snapshots record inner_relief_pending=true and inner_relief_applied=false. Increasing the diameter to a valid drawing-based value creates the additional relief. A manual override is preserved when the bearing bore changes; zero or other invalid manual diameters still produce an error.

Enabling Inner-ring relief while its manual diameter is still 0 mm correctly disables creation; enter a drawing-based value first. With the owner's reported bore 8 mm, allowance 0.5 mm and contact diameter 21.9 mm, the geometric interval is strictly greater than 8.5 mm and less than 21.9 mm. This interval does not prescribe a manufacturer-safe relief diameter. The current error text displays both limits and the entered value.

For Blind mode, the shaft pocket must extend deeper than the seat and any enabled inner-ring relief. An equal or shallower depth is rejected. Through All ignores the inactive blind-depth field and uses Fusion's native through-all extent on the selected body.

## Geometry and preflight

Each optional operation has its own circular sketch. Profile calculation remains enabled through construction and cutting; sketches are hidden after their final cut. Relief start offsets use the signed inward distance from the original face plane, so both upward- and downward-facing sketches are handled explicitly.

Before the first cut, every seat, blind shaft and relief validation tool must fit inside the original body, including the remaining-floor check. Through All intentionally exits the body: its finite preflight envelope covers the body's projected bounding-box depth plus 1 mm, while the final cut uses the native through-all extent with explicit participantBodies. Through All does not require a closed floor and is not a blind-pocket containment check.

Pairwise batch checks include every seat/shaft/relief envelope. All validation extrusions are deleted before final direct cuts. A failure in an optional operation or snapshot write removes the entire batch and marks the command transaction failed. A successful seat snapshot stores the actual bore, selected modes and all clearance feature/sketch references; no inner-ring bearing dimension is inferred from the manually entered relief diameter.

## Live acceptance checklist

- UI regression in 0.1.8: select a face and confirm focus moves to Seat positions. Enable a shaft and inner-ring relief: its initial diameter equals Bearing bore and the seat/shaft preview remains available with the pending message. Change bore and confirm the preset follows; manually enter a valid relief diameter and verify it survives later bore changes. Parameter edits must not steal selection focus.

1. Test Off: the confirmed seat-only geometry remains unchanged.
2. Test Blind with the example above. Measure the opening diameter, face-referenced blind depth, floor-referenced relief depth and support annulus.
3. Test Through All in 0.1.7: check the shaft exits the selected body and no neighboring body is cut. Repeat with both sketch-normal orientations; a missing shaft must produce an error rather than a valid preview. If an error remains, record its complete Fusion warning/error text.
4. Repeat on a bottom-facing and inclined face to verify the offset direction.
5. Try an unknown/zero relief diameter, a relief smaller than the shaft, insufficient support geometry and a blind depth ending above the relief. Each invalid batch must be rejected without partial cuts.
6. Preview multiple positions, change modes and dimensions, cancel, then create. Verify no validation tools remain and undo removes the whole batch in one step.
7. Test a relief or blind depth that breaks out. Also verify that an intentional Through All exit is accepted.
8. Inspect saved snapshots after saving/reopening a disposable design. Reopening/editing through the BearingNest UI is still pending.

Chamfer and seat editing remain the next implementation steps. The full 0.2.0 milestone is not complete.
