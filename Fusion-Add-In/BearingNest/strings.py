"""English source strings, centralized for later localization."""

TEXT = {
    'description': 'Print-oriented ball bearing seats with rounded reliefs and an odd number of contact lands.',
    'bearing_seat': 'Bearing Seat',
    'settings': 'Settings',
    'about': 'Info',
    'missing_panel': 'The Solid tab Create panel in the Design workspace is unavailable.',
    'foundation_status': '<b>Version {version} - Seat prototype</b><br>Select a planar face and one or more positions in the root component. All positions share the same bearing and contour values.',
    'workflow': '<b>Planned workflow</b><br>1. Select a planar face and seat positions.<br>2. Choose a bearing and adjust the fit.<br>3. Review the preview and create the seats.',
    'geometry_status': 'Blind depth starts at the selected face; inner-ring relief starts at the seat floor. Chamfer size is the equal axial/radial leg (0 = off). Edit the last complete batch using the list above; all its seats share the edited values.',
    'settings_status': 'Manage reusable print profiles and transfer local data here. Choose the profile and Auto options for the current seat on Bearing Seat. Library changes are saved immediately, even if geometry is cancelled.',
    'profile_guidance': 'Save a profile under an existing name to update it, or use a new name to create one. Profile changes affect only Auto fields. Manual fields remain unchanged. Wall warnings use conservative enclosing cylinders; they are advisory, not a measured minimum wall thickness. Defaults and factors require printed trials.',
    'parameter_help': '<b>Parameter conventions</b><br>Dimensions are in millimetres; angles are in degrees.<br>Negative diameter correction tightens the fit.<br>Positive axial correction recesses the bearing; negative correction makes it protrude.',
    'printing_help': 'Print-derived dimensions are provisional. Layer-based relief depths correspond to print layers only when the seat axis aligns with print Z.',
    'limitations': 'Prototype: one planar root-component face in a parametric design. Editing rebuilds the last complete batch and requires no later features or timeline groups. Chamfer checks and advisory wall probes use conservative enclosing cylinders. Through All shaft exit and lateral shaft walls are excluded from wall probes. No assemblies. Verify bearing dimensions and outer-ring support against a drawing.',
    'catalog_search': 'Find bearing',
    'catalog_bearing': 'Bearing catalog (d x D x B)',
    'manual_bearing': 'Manual dimensions',
    'print_profile': 'Print profile',
    'saved_profile': 'Stored seat profile snapshot',
    'saved_bearing': 'Stored/current bearing snapshot (manual overrides retained)',
    'relief_mm_auto': 'Auto radial relief depth',
    'fillet_mm_auto': 'Auto transition radius',
    'inner_depth_mm_auto': 'Auto inner-ring relief depth',
    'profile_reset': 'Reset all three fields to suggested values',
    'effective_profile': '<b>{name}</b>: nozzle {nozzle:g} mm, layer {layer:g} mm.<br>Suggestions: relief {rf:g} x nozzle = {relief:g} mm; radius {ff:g} x nozzle = {fillet:g} mm; inner depth {df:g} x layer = {depth:g} mm.<br>Advisory wall margin: {wall:g} mm. Conservative envelope check; not a minimum-thickness measurement. Provisional; verify contour feasibility.',
    'wall_body_warning': 'Position {index}: possible wall/floor margin below {threshold:g} mm near the body boundary or an existing void (conservative envelope). Creation remains allowed.',
    'wall_pair_warning': 'Positions {first} and {second}: possible intervening wall below {threshold:g} mm (conservative envelopes). Creation remains allowed.',
    'wall_check_unavailable': 'Position {index}: the advisory wall check could not be completed. Inspect walls manually; creation remains allowed.',
    'wall_warning_heading': 'Advisory wall warnings',
    'marker_legend': 'Approximate envelope markers: red = invalid; amber = wall warning; blue = other resolved positions in a rejected batch. An invalid position blocks the whole batch.',
    'marker_cleanup_failed': 'Could not remove BearingNest preview markers. Cancel the command before retrying.',
    'marker_creation_failed': 'Could not draw the preview markers.',
    'markers_unavailable': 'Preview markers unavailable: {error}. Text diagnostics remain authoritative.',
    'custom_id': 'Custom ID (empty = new)',
    'custom_inner_mm': 'Drawing inner-ring outside diameter (0 = unknown)',
    'bearing_load': 'Load selected bearing metadata',
    'bearing_save': 'Save bearing',
    'bearing_delete': 'Delete selected bearing',
    'profile_name': 'Print profile name',
    'profile_save': 'Save and use named profile',
    'profile_delete': 'Delete selected print profile',
    'settings_file': 'Absolute JSON import/export path',
    'settings_import': 'Import and merge JSON',
    'settings_export': 'Export JSON to a new file',
    'settings_load_error': 'Settings could not be loaded: {error}<br>The file is preserved. Repair or move it before saving settings. Seats can still use manual dimensions and the provisional profile.',
    'settings_location': 'Local settings: {path}<br>Built-in records are size aliases with verified d/D/B only. Unknown inner-ring dimensions remain unknown. Purchasing URLs are stored as text and are never opened automatically.',
    'settings_saved': 'Settings action completed. Existing seats keep their own snapshots. Apply Seats is required to update the current batch.',
    'repair_settings': 'Repair or move the unreadable settings file and reopen the command before saving.',
    'invalid_settings_expression': 'Enter valid dimensions and factors before saving.',
    'choose_bearing': 'Select a catalog bearing first.',
    'choose_local_profile': 'Select a profile from the local library before deleting.',
    'custom_identity_required': 'Use an existing custom ID to update/delete, or an empty ID to create a record. Built-in aliases cannot be changed.',
    'absolute_json_path': 'Enter an absolute path ending in .json.',
    'separate_transfer_path': 'Use a separate file for import/export, not the active settings file.',
    'export_exists': 'Export destination already exists. Choose a new filename.',
    'import_missing': 'The import file does not exist.',
    'select_face': 'Planar face',
    'select_face_prompt': 'Select a planar face on a solid body in the root component.',
    'select_position': 'Seat positions',
    'select_position_prompt': 'Select one or more sketch points, vertices or circular edge centers on the face plane.',
    'land_count': 'Contact lands',
    'preview': 'Preview',
    'shaft_mode': 'Shaft opening',
    'inner_relief_enabled': 'Inner-ring relief',
    'inner_relief_pending': 'Bore preset: no additional inner-ring cut. Enter a larger drawing-based diameter for relief; seat and shaft remain previewable.',
    'create_seat': 'Apply Seats',
    'edit_batch': 'Create or edit seats',
    'new_batch': 'Create new seats',
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
    ('chamfer_mm', '45 deg lead-in chamfer (0 = off)', 'mm', '0.4 mm'),
    ('bore_mm', 'Bearing bore (manual)', 'mm', '8 mm'),
    ('shaft_allowance_mm', 'Shaft diameter allowance', 'mm', '0.2 mm'),
    ('blind_depth_mm', 'Blind shaft depth from face', 'mm', '12 mm'),
    ('inner_diameter_mm', 'Inner-ring relief diameter (manual)', 'mm', '8 mm'),
    ('inner_depth_mm', 'Inner-ring relief depth from seat floor', 'mm', '0.4 mm'),
)

PROFILE_FIELDS = (
    ('nozzle_mm', 'Nozzle diameter', 'mm'),
    ('layer_mm', 'Layer height', 'mm'),
    ('relief_factor', 'Radial relief / nozzle factor', ''),
    ('fillet_factor', 'Transition radius / nozzle factor', ''),
    ('inner_depth_factor', 'Inner depth / layer factor', ''),
    ('wall_factor', 'Advisory wall margin / nozzle factor', ''),
)

BEARING_TEXT_FIELDS = (
    ('designation', 'Bearing designation'),
    ('manufacturer', 'Manufacturer (empty = size alias)'),
    ('part_number', 'Manufacturer part number'),
    ('source', 'Source reference / drawing'),
    ('notes', 'Bearing notes'),
    ('purchasing_url', 'Optional purchasing URL'),
)

TEXT.update(catalog_save_name='Bearing name', catalog_save='Save parameters to bearing catalog',
            catalog_name_required='Enter a bearing name before saving.',
            catalog_parameters_saved='Bearing parameters saved to the local catalog.',
            edit_batch_label='Edit batch {number}: {count} seat(s) [{identity}]',
            repair_seats='Some saved seats need repair: {errors}',
            invalid_expression='{label}: invalid expression.',
            saved_bearing_name='Saved bearing', size_alias='size alias')
TEXT.update(
    catalog_tab='Bearing Catalog',
    catalog_search_help='Filter the bearing list below by designation, manufacturer or dimensions. Examples: 608, SKF, 8 22 7. Clear the field to show all bearings.',
    seat_profile_group='Print profile for this seat',
    seat_fit_group='Fit and lead-in',
    seat_contour_group='Contact lands and reliefs',
    seat_shaft_group='Shaft opening',
    seat_relief_group='Inner-ring relief',
    bearing_data_group='Designation and source',
    bearing_dimensions_group='Bearing dimensions',
    bearing_preset_group='Saved seat parameters',
    profiles_group='Reusable print profiles',
    transfer_group='Import / export',
    new_catalog_bearing='New bearing',
    catalog_help='Select a bearing to edit dimensions, metadata and saved seat parameters. Choose New bearing to create an entry. Save and delete take effect immediately, independently of Apply Seats or Cancel. The current seat keeps its own values.',
    catalog_builtin_copy='Built-in sizes are read-only. Saving creates an editable custom copy.',
    catalog_action_saved='Catalog updated. Current and existing seats retain their own values; select the bearing again on Bearing Seat to load the updated preset.',
    project_links='<b>Project and support</b><br><a href="https://github.com/know-how-schmiede/BearingNest">Download BearingNest</a><br><a href="https://github.com/know-how-schmiede/BearingNest/issues">Report a bug</a><br><a href="https://www.youtube.com/@knowhowschmiede">YouTube: Know-How-Schmiede</a><br><a href="https://www.know-how-schmiede.de/">www.know-how-schmiede.de</a>',
)
ENGLISH_TEXT = dict(TEXT)
PARAMETER_FIELDS = list(PARAMETER_FIELDS)
PROFILE_FIELDS = list(PROFILE_FIELDS)
BEARING_TEXT_FIELDS = list(BEARING_TEXT_FIELDS)
_FIELD_SOURCES = [tuple(fields) for fields in
                  (PARAMETER_FIELDS, PROFILE_FIELDS, BEARING_TEXT_FIELDS)]
_locale = 'en'


def label(source):
    if _locale == 'de':
        from .strings_de import LABELS
        return LABELS.get(source, source)
    return source


def source_label(display):
    for source in ('Off', 'Through All', 'Blind'):
        if display == label(source):
            return source
    return display


def set_locale(locale):
    global _locale
    _locale = 'de' if locale.lower().replace('_', '-').split('-')[0] == 'de' else 'en'
    TEXT.clear()
    TEXT.update(ENGLISH_TEXT)
    if _locale == 'de':
        from .strings_de import TEXT as german
        TEXT.update(german)
    for fields, sources in zip((PARAMETER_FIELDS, PROFILE_FIELDS, BEARING_TEXT_FIELDS), _FIELD_SOURCES):
        fields[:] = [(row[0], label(row[1]), *row[2:]) for row in sources]


def configure_from_fusion(app):
    """Use Fusion's UI preference; hosts without preferences use English."""
    import adsk.core
    try:
        german = app.preferences.generalPreferences.userLanguage == adsk.core.UserLanguages.GermanLanguage
    except AttributeError:
        german = False
    set_locale('de' if german else 'en')
