"""English source strings, centralized for later localization."""

TEXT = {
    'description': 'Print-oriented ball bearing seats with rounded reliefs and an odd number of contact lands.',
    'bearing_seat': 'Bearing Seat',
    'settings': 'Settings',
    'about': 'About',
    'missing_panel': 'The Solid tab Create panel in the Design workspace is unavailable.',
    'foundation_status': '<b>Version {version} - Seat prototype</b><br>Select a planar face and one or more positions in the root component. All positions share the same bearing and contour values.',
    'workflow': '<b>Planned workflow</b><br>1. Select a planar face and seat positions.<br>2. Choose a bearing and adjust the fit.<br>3. Review the preview and create the seats.',
    'geometry_status': 'All positions are checked before cutting; invalid or overlapping seats block the whole batch. Shaft opening, inner-ring relief, chamfer and editing are not available yet. Cancel rolls back the preview.',
    'settings_status': '<b>Library and print profiles</b><br>Library management, named print profiles and import/export are planned for version 0.3.0. No settings are saved in version {version}.',
    'profile_guidance': '<b>Planned print settings</b><br>Nozzle diameter and layer height will suggest relief dimensions. Manual overrides will be kept when changing profiles. Proposed defaults require printed trials.',
    'parameter_help': '<b>Parameter conventions</b><br>Dimensions are in millimetres; angles are in degrees.<br>Negative diameter correction tightens the fit.<br>Positive axial correction recesses the bearing; negative correction makes it protrude.',
    'printing_help': 'Print-derived dimensions are provisional. Layer-based relief depths correspond to print layers only when the seat axis aligns with print Z.',
    'limitations': 'Prototype: multiple positions on one planar root-component face in a parametric design. No assemblies, catalog, shaft opening, inner-ring relief, chamfer or seat editing yet. Bearing dimensions are manual and require verification.',
    'select_face': 'Planar face',
    'select_face_prompt': 'Select a planar face on a solid body in the root component.',
    'select_position': 'Seat positions',
    'select_position_prompt': 'Select one or more sketch points, vertices or circular edge centers on the face plane.',
    'land_count': 'Contact lands',
    'preview': 'Preview',
    'create_seat': 'Create Seats',
    'selection_required': 'Select one planar face and at least one seat position.',
    'design_required': 'Open a parametric Fusion design before creating a seat.',
    'ready': '{count} position(s). Contact diameter: {diameter:.3f} mm; seat depth: {depth:.3f} mm. Containment and overlap are checked during preview and creation.',
    'preview_ready': 'Preview valid for {count} seat(s). Contact diameter: {diameter:.3f} mm; seat depth: {depth:.3f} mm.',
}

# Attribute name, English label, explicit units, default expression.
PARAMETER_FIELDS = (
    ('outside_mm', 'Bearing outside diameter', 'mm', '22 mm'),
    ('width_mm', 'Bearing width', 'mm', '7 mm'),
    ('correction_mm', 'Diameter correction', 'mm', '-0.10 mm'),
    ('axial_mm', 'Axial correction', 'mm', '0 mm'),
    ('land_degrees', 'Contact land angle', 'deg', '30 deg'),
    ('rotation_degrees', 'Pattern rotation', 'deg', '0 deg'),
    ('relief_mm', 'Radial relief depth', 'mm', '1.2 mm'),
    ('fillet_mm', 'Transition radius', 'mm', '0.4 mm'),
)
