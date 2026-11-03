"""BearingNest foundation dialog; no model changes in version 0.1.0."""
import os
import adsk.core
from ...lib import fusionAddInUtils as futil
from ... import config
from ...version import VERSION
from ...strings import TEXT

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_bearingSeat'
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'
LEGACY_PANEL_ID = 'SolidScriptsAddinsPanel'
RESOURCE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')
ICON_FOLDER = os.path.join(RESOURCE_FOLDER, 'toolbar', '')
local_handlers = []
_definition_handlers = []


def _panel(panel_id=PANEL_ID):
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    return workspace.toolbarPanels.itemById(panel_id) if workspace else None


def _remove_legacy_control():
    panel = _panel(LEGACY_PANEL_ID)
    control = panel.controls.itemById(CMD_ID) if panel else None
    if control:
        control.deleteMe()


def start():
    """Register one command, including when called twice without a stop."""
    panel = _panel()
    if not panel:
        raise RuntimeError(TEXT['missing_panel'])
    _remove_legacy_control()
    definition = ui.commandDefinitions.itemById(CMD_ID)
    try:
        if not definition:
            definition = ui.commandDefinitions.addButtonDefinition(
                CMD_ID, f'{config.ADDIN_NAME} {VERSION}', TEXT['description'], ICON_FOLDER)
            futil.add_handler(definition.commandCreated, command_created,
                              local_handlers=_definition_handlers)
        definition.name = f'{config.ADDIN_NAME} {VERSION}'
        control = panel.controls.itemById(CMD_ID)
        if not control:
            control = panel.controls.addCommand(definition)
        control.isPromotedByDefault = True
        control.isPromoted = True
    except Exception:
        stop()
        raise


def stop():
    """Remove toolbar UI and release template event handler references."""
    _remove_legacy_control()
    panel = _panel()
    control = panel.controls.itemById(CMD_ID) if panel else None
    if control:
        control.deleteMe()
    definition = ui.commandDefinitions.itemById(CMD_ID)
    if definition:
        definition.deleteMe()
    _definition_handlers.clear()
    local_handlers.clear()


def _text(inputs, identity, key, rows):
    field = inputs.addTextBoxCommandInput(
        identity, '', TEXT[key].format(version=VERSION), rows, True)
    field.isFullWidth = True
    return field


def command_created(args: adsk.core.CommandCreatedEventArgs):
    command = args.command
    command.isOKButtonVisible = False
    command.setDialogInitialSize(520, 480)
    futil.add_handler(command.destroy, command_destroy, local_handlers=local_handlers)
    inputs = command.commandInputs

    seat = inputs.addTabCommandInput('bearing_seat_tab', TEXT['bearing_seat']).children
    _text(seat, 'foundation_status', 'foundation_status', 3)
    _text(seat, 'workflow', 'workflow', 5)
    _text(seat, 'geometry_status', 'geometry_status', 3)

    settings = inputs.addTabCommandInput('settings_tab', TEXT['settings']).children
    _text(settings, 'settings_status', 'settings_status', 4)
    _text(settings, 'profile_guidance', 'profile_guidance', 5)

    about = inputs.addTabCommandInput('about_tab', TEXT['about']).children
    logo = about.addImageCommandInput(
        'bearingnest_logo', '', os.path.join(RESOURCE_FOLDER, 'logo.png'))
    logo.isFullWidth = True
    version = about.addTextBoxCommandInput(
        'version', '', f'<b>{config.ADDIN_NAME} {VERSION}</b>', 1, True)
    version.isFullWidth = True
    _text(about, 'purpose', 'description', 2)
    _text(about, 'parameter_help', 'parameter_help', 5)
    _text(about, 'printing_help', 'printing_help', 3)
    _text(about, 'limitations', 'limitations', 3)


def command_destroy(args: adsk.core.CommandEventArgs):
    local_handlers.clear()
