"""BearingNest registration and seat, catalog, settings and info dialog."""
import os
import adsk.core
from ...lib import fusionAddInUtils as futil
from ... import config
from ...version import VERSION
from ...strings import TEXT, configure_from_fusion
from .seat_dialog import SeatDialog
from .catalog_dialog import CatalogDialog

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
_dialogs = []


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
    configure_from_fusion(app)
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
    _clear_dialogs()


def _text(inputs, identity, key, rows):
    field = inputs.addTextBoxCommandInput(
        identity, '', TEXT[key].format(version=VERSION), rows, True)
    field.isFullWidth = True
    return field


def command_created(args: adsk.core.CommandCreatedEventArgs):
    command = args.command
    command.isOKButtonVisible = True
    command.okButtonText = TEXT['create_seat']
    command.setDialogInitialSize(540, 650)
    futil.add_handler(command.destroy, command_destroy, local_handlers=local_handlers)
    inputs = command.commandInputs

    seat = inputs.addTabCommandInput('bearing_seat_tab', TEXT['bearing_seat']).children
    dialog = SeatDialog(seat, app)
    _dialogs.append(dialog)
    for event, callback in ((command.validateInputs, dialog.validate),
                            (command.inputChanged, dialog.changed),
                            (command.executePreview, dialog.preview),
                            (command.execute, dialog.execute)):
        futil.add_handler(event, callback, local_handlers=local_handlers)

    catalog = inputs.addTabCommandInput('catalog_tab', TEXT['catalog_tab']).children
    settings = inputs.addTabCommandInput('settings_tab', TEXT['settings']).children
    _text(settings, 'settings_status', 'settings_status', 4)
    dialog._refreshing = True
    try:
        dialog.catalog = CatalogDialog(seat, settings, dialog, catalog)
    finally:
        dialog._refreshing = False

    about = inputs.addTabCommandInput('about_tab', TEXT['about']).children
    logo = about.addImageCommandInput(
        'bearingnest_logo', '', os.path.join(RESOURCE_FOLDER, 'logo.png'))
    logo.isFullWidth = True
    version = about.addTextBoxCommandInput(
        'version', '', f'<b>{config.ADDIN_NAME} {VERSION}</b>', 1, True)
    version.isFullWidth = True
    _text(about, 'purpose', 'description', 2)
    _text(about, 'project_links', 'project_links', 5)
    _text(about, 'parameter_help', 'parameter_help', 5)
    _text(about, 'printing_help', 'printing_help', 3)
    _text(about, 'limitations', 'limitations', 3)


def command_destroy(args: adsk.core.CommandEventArgs):
    local_handlers.clear()
    _clear_dialogs()


def _clear_dialogs():
    failures = []
    for dialog in list(_dialogs):
        try:
            dialog.clear_feedback()
            _dialogs.remove(dialog)
        except Exception as error:
            failures.append(str(error))
    if failures:
        raise RuntimeError('; '.join(failures))
