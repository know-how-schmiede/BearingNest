"""English source strings, centralized for later localization."""

TEXT = {
    'description': 'Print-oriented ball bearing seats with rounded reliefs and an odd number of contact lands.',
    'bearing_seat': 'Bearing Seat',
    'settings': 'Settings',
    'about': 'About',
    'missing_panel': 'The Design workspace Add-Ins panel is unavailable.',
    'foundation_status': '<b>Version {version} - Foundation</b><br>The dialog foundation is available. Seat creation is planned for a later milestone.',
    'workflow': '<b>Planned workflow</b><br>1. Select a planar face and seat positions.<br>2. Choose a bearing and adjust the fit.<br>3. Review the preview and create the seats.',
    'geometry_status': 'Face selection, bearing parameters, geometry, preview and editing are not available in this version. Closing this dialog leaves the design unchanged.',
    'settings_status': '<b>Library and print profiles</b><br>Library management, named print profiles and import/export are planned for version 0.3.0. No settings are saved in version {version}.',
    'profile_guidance': '<b>Planned print settings</b><br>Nozzle diameter and layer height will suggest relief dimensions. Manual overrides will be kept when changing profiles. Proposed defaults require printed trials.',
    'parameter_help': '<b>Parameter conventions</b><br>Dimensions are in millimetres; angles are in degrees.<br>Negative diameter correction tightens the fit.<br>Positive axial correction recesses the bearing; negative correction makes it protrude.',
    'printing_help': 'Print-derived dimensions are provisional. Layer-based relief depths correspond to print layers only when the seat axis aligns with print Z.',
    'limitations': 'Geometry and persistent editing begin with the 0.2.0 prototype. Bearing catalog dimensions require manufacturer verification. See the documentation supplied with the project.',
}
