"""Isolated lifecycle checks; actual Fusion behavior requires manual checks."""
import importlib
import json
import math
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1] / 'Fusion-Add-In' / 'BearingNest'


class Items:
    def __init__(self):
        self.items = {}

    def itemById(self, identity):
        return self.items.get(identity)

    def add(self, identity, **attributes):
        item = SimpleNamespace(**attributes)
        item.deleteMe = lambda: self.items.pop(identity, None)
        self.items[identity] = item
        return item

    def addButtonDefinition(self, identity, name, description, resources):
        return self.add(identity, id=identity, name=name, commandCreated=object())

    def addCommand(self, definition):
        return self.add(definition.id)


class Inputs:
    def __init__(self):
        self.tabs = []
        self.fields = []

    def addTabCommandInput(self, identity, label):
        tab = SimpleNamespace(id=identity, label=label, children=Inputs())
        self.tabs.append(tab)
        return tab

    def addTextBoxCommandInput(self, identity, label, text, rows, readonly):
        field = SimpleNamespace(id=identity, text=text, readonly=readonly)
        self.fields.append(field)
        return field

    def addImageCommandInput(self, identity, label, filename):
        if not Path(filename).is_file():
            raise FileNotFoundError(filename)
        return SimpleNamespace()

    def addSelectionInput(self, identity, label, prompt):
        field = SimpleNamespace(id=identity, filters=[], selectionCount=0)
        field.addSelectionFilter = field.filters.append
        field.setSelectionLimits = lambda minimum, maximum: setattr(field, 'limits', (minimum, maximum))
        self.fields.append(field)
        return field

    def addValueInput(self, identity, label, units, expression):
        number = float(expression.split()[0])
        value = math.radians(number) if units == 'deg' else number / 10
        field = SimpleNamespace(id=identity, value=value, isValidExpression=True)
        self.fields.append(field)
        return field

    def addDropDownCommandInput(self, identity, label, style):
        field = SimpleNamespace(id=identity, selectedItem=None)
        def add(name, selected, icon):
            if selected:
                field.selectedItem = SimpleNamespace(name=name)
        field.listItems = SimpleNamespace(add=add)
        self.fields.append(field)
        return field

    def addBoolValueInput(self, identity, label, checkbox, resource, initial):
        field = SimpleNamespace(id=identity, value=initial)
        self.fields.append(field)
        return field


class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.definitions = Items()
        self.controls = Items()
        self.workspace = SimpleNamespace(toolbarPanels=Items())
        self.workspace.toolbarPanels.items['SolidCreatePanel'] = SimpleNamespace(
            controls=self.controls)
        self.legacy_controls = Items()
        self.workspace.toolbarPanels.items['SolidScriptsAddinsPanel'] = SimpleNamespace(
            controls=self.legacy_controls)
        self.ui = SimpleNamespace(commandDefinitions=self.definitions, workspaces=Items())
        self.ui.workspaces.items['FusionSolidEnvironment'] = self.workspace
        core = ModuleType('adsk.core')
        core.Application = SimpleNamespace(get=lambda: SimpleNamespace(userInterface=self.ui))
        core.CommandCreatedEventArgs = object
        core.CommandEventArgs = object
        core.ValueInput = SimpleNamespace(createByString=lambda expression: expression)
        core.DropDownStyles = SimpleNamespace(TextListDropDownStyle=0)
        adsk = ModuleType('adsk')
        adsk.core = core
        self.callbacks = []

        def add_handler(event, callback, *, local_handlers):
            local_handlers.append(callback)
            self.callbacks.append(callback)

        utilities = ModuleType('foundation.lib.fusionAddInUtils')
        utilities.add_handler = add_handler
        package = ModuleType('foundation')
        package.__path__ = [str(ROOT)]
        commands = ModuleType('foundation.commands')
        commands.__path__ = [str(ROOT / 'commands')]
        self.modules = patch.dict(sys.modules, {
            'adsk': adsk, 'adsk.core': core, 'foundation': package,
            'foundation.commands': commands,
            'foundation.lib.fusionAddInUtils': utilities,
        })
        self.modules.start()
        self.entry = importlib.import_module('foundation.commands.commandDialog.entry')

    def tearDown(self):
        self.modules.stop()

    def test_repeated_start_and_stop_leave_no_duplicate_ui_or_handlers(self):
        self.entry.start()
        self.entry.start()
        self.assertEqual(len(self.definitions.items), 1)
        self.assertEqual(len(self.controls.items), 1)
        self.assertEqual(len(self.entry._definition_handlers), 1)
        self.assertEqual(self.definitions.itemById(self.entry.CMD_ID).name,
                         f'BearingNest {self.entry.VERSION}')
        self.entry.stop()
        self.entry.stop()
        self.assertFalse(self.definitions.items)
        self.assertFalse(self.controls.items)
        self.assertFalse(self.entry._definition_handlers)
        self.entry.start()
        self.assertEqual(len(self.entry._definition_handlers), 1)
        self.entry.stop()

    def test_missing_panel_does_not_leave_a_command_definition(self):
        self.ui.workspaces.items.clear()
        with self.assertRaises(RuntimeError):
            self.entry.start()
        self.assertFalse(self.definitions.items)
        self.entry.stop()

    def test_registration_migrates_from_utilities_to_solid_create(self):
        self.legacy_controls.add(self.entry.CMD_ID)
        self.entry.start()
        self.assertFalse(self.legacy_controls.items)
        control = self.controls.itemById(self.entry.CMD_ID)
        self.assertTrue(control.isPromoted)
        self.assertTrue(control.isPromotedByDefault)
        self.assertTrue(Path(self.entry.ICON_FOLDER, '32x32.svg').is_file())
        self.entry.stop()

    def test_failed_control_registration_cleans_up_definition_and_handlers(self):
        with patch.object(self.controls, 'addCommand', side_effect=RuntimeError('failed')):
            with self.assertRaises(RuntimeError):
                self.entry.start()
        self.assertFalse(self.definitions.items)
        self.assertFalse(self.entry._definition_handlers)

    def make_dialog(self):
        inputs = Inputs()
        command = SimpleNamespace(commandInputs=inputs, destroy=object(),
                                  validateInputs=object(), inputChanged=object(),
                                  executePreview=object(), execute=object(),
                                  setDialogInitialSize=lambda width, height: None)
        self.entry.command_created(SimpleNamespace(command=command))
        dialog = next(callback.__self__ for callback in self.callbacks
                      if callback.__name__ == 'execute')
        return command, inputs, dialog

    def test_dialog_has_three_tabs_required_selections_and_handler_cleanup(self):
        command, inputs, dialog = self.make_dialog()
        self.assertEqual([tab.label for tab in inputs.tabs],
                         ['Bearing Seat', 'Settings', 'About'])
        self.assertTrue(command.isOKButtonVisible)
        self.assertEqual(command.okButtonText, 'Create Seats')
        self.assertEqual(dialog.fields['seat_position'].limits, (1, 0))
        self.assertEqual(dialog.fields['seat_face'].filters, ['PlanarFaces'])
        self.assertIn('CircularEdges', dialog.fields['seat_position'].filters)
        self.assertFalse(dialog.fields['seat_preview'].value)
        self.assertTrue(self.entry.local_handlers)
        self.entry.command_destroy(None)
        self.assertFalse(self.entry.local_handlers)

    def test_execute_failure_marks_entire_command_transaction_for_abort(self):
        command, inputs, dialog = self.make_dialog()
        geometry = ModuleType('foundation.seat_geometry')
        geometry.create_seats = Mock(side_effect=RuntimeError('snapshot failed'))
        args = SimpleNamespace()
        with patch.dict(sys.modules, {'foundation.seat_geometry': geometry}), \
                patch.object(dialog, '_request', return_value=(1, 2, 3, 4)):
            dialog.execute(args)
        self.assertTrue(args.executeFailed)
        self.assertEqual(args.executeFailedMessage, 'snapshot failed')

    def test_preview_is_opt_in_and_cannot_be_committed_without_execute(self):
        command, inputs, dialog = self.make_dialog()
        geometry = ModuleType('foundation.seat_geometry')
        geometry.create_seats = Mock()
        args = SimpleNamespace(isValidResult=True)
        parameters = SimpleNamespace(contact_mm=21.9, depth_mm=7)
        with patch.dict(sys.modules, {'foundation.seat_geometry': geometry}), \
                patch.object(dialog, '_request', return_value=(1, 2, [3], parameters)):
            dialog.preview(args)
            geometry.create_seats.assert_not_called()
            dialog.fields['seat_preview'].value = True
            dialog.preview(args)
        self.assertFalse(args.isValidResult)
        geometry.create_seats.assert_called_once_with(1, 2, [3], parameters, persist=False)

    def test_dialog_converts_internal_length_and_angle_units_before_model_validation(self):
        command, inputs, dialog = self.make_dialog()
        geometry = ModuleType('foundation.seat_geometry')
        geometry.placement = Mock()
        fusion = ModuleType('adsk.fusion')
        fusion.Design = SimpleNamespace(cast=lambda value: value)
        dialog.app.activeProduct = object()
        for identity in ('seat_face', 'seat_position'):
            dialog.fields[identity].selectionCount = 1
            dialog.fields[identity].selection = lambda index: SimpleNamespace(entity=object())
        dialog.fields['seat_position'].selectionCount = 3
        with patch.dict(sys.modules, {'foundation.seat_geometry': geometry, 'adsk.fusion': fusion}), \
                patch.object(sys.modules['adsk'], 'fusion', fusion, create=True):
            request = dialog._request()
        parameters = request[-1]
        self.assertEqual(len(request[2]), 3)
        self.assertEqual(geometry.placement.call_count, 3)
        self.assertEqual(parameters.outside_mm, 22)
        self.assertAlmostEqual(parameters.correction_mm, -0.1)
        self.assertAlmostEqual(parameters.land_degrees, 30)
        self.assertAlmostEqual(parameters.relief_mm, 1.2)

    def test_manifest_and_runtime_versions_match(self):
        manifest = json.loads((ROOT / 'BearingNest.manifest').read_text(encoding='utf-8-sig'))
        self.assertEqual(manifest['version'], self.entry.VERSION)
        self.assertTrue((ROOT / manifest['iconFilename']).is_file())

    def test_validation_enables_create_without_writing_any_dialog_input(self):
        command, inputs, dialog = self.make_dialog()
        class ReadOnlyStatus:
            @property
            def formattedText(self):
                return 'unchanged'
            @formattedText.setter
            def formattedText(self, value):
                raise AssertionError('Dialog inputs must not be changed during validation')
        dialog.status = ReadOnlyStatus()
        args = SimpleNamespace(areInputsValid=False)
        with patch.object(dialog, '_request', return_value=(1, 2, [3], object())) as request:
            dialog.validate(args)
        self.assertTrue(args.areInputsValid)
        request.assert_called_once_with(check_placement=False)

    def test_input_edit_clears_old_preview_error_and_recovers_create(self):
        command, inputs, dialog = self.make_dialog()
        dialog.geometry_error = 'previous preview failed'
        parameters = SimpleNamespace(contact_mm=21.9, depth_mm=7)
        args = SimpleNamespace(areInputsValid=False)
        with patch.object(dialog, '_request', return_value=(1, 2, [3, 4], parameters)):
            dialog.changed(SimpleNamespace(input=SimpleNamespace(id='outside_mm')))
            dialog.validate(args)
        self.assertIsNone(dialog.geometry_error)
        self.assertTrue(args.areInputsValid)
        self.assertIn('2 position', dialog.status.formattedText)

    def test_unchanged_status_does_not_invalidate_inputs_again(self):
        command, inputs, dialog = self.make_dialog()
        status = Mock()
        dialog.status = status
        with patch.object(type(dialog), '_set_status', wraps=dialog._set_status):
            dialog._set_status('Ready')
            # A repeated call must not change the underlying status property.
            status.formattedText = 'sentinel'
            dialog._set_status('Ready')
        self.assertEqual(status.formattedText, 'sentinel')

    def test_failed_preview_is_retried_successfully_without_stale_error_latching(self):
        command, inputs, dialog = self.make_dialog()
        dialog.fields['seat_preview'].value = True
        geometry = ModuleType('foundation.seat_geometry')
        geometry.create_seats = Mock(side_effect=[RuntimeError('preview failure'), []])
        parameters = SimpleNamespace(contact_mm=21.9, depth_mm=7)
        args = SimpleNamespace(isValidResult=True)
        with patch.dict(sys.modules, {'foundation.seat_geometry': geometry}), \
                patch.object(dialog, '_request', return_value=(1, 2, [3], parameters)):
            dialog.preview(args)
            invalid = SimpleNamespace(areInputsValid=True)
            dialog.validate(invalid)
            self.assertFalse(invalid.areInputsValid)
            dialog.preview(args)
            valid = SimpleNamespace(areInputsValid=False)
            dialog.validate(valid)
        self.assertIsNone(dialog.geometry_error)
        self.assertTrue(valid.areInputsValid)
        self.assertFalse(args.isValidResult)

    def test_optional_clearance_controls_follow_modes_outside_validation(self):
        command, inputs, dialog = self.make_dialog()
        self.assertFalse(dialog.fields['bore_mm'].isEnabled)
        self.assertFalse(dialog.fields['inner_diameter_mm'].isEnabled)
        dialog.fields['shaft_mode'].selectedItem.name = 'Blind'
        dialog._refresh_controls()
        self.assertTrue(dialog.fields['bore_mm'].isEnabled)
        self.assertTrue(dialog.fields['blind_depth_mm'].isEnabled)
        dialog.fields['inner_relief_enabled'].value = True
        dialog._refresh_controls()
        self.assertTrue(dialog.fields['inner_diameter_mm'].isEnabled)

    def test_turning_shaft_off_ignores_inactive_relief_values_and_checked_preference(self):
        command, inputs, dialog = self.make_dialog()
        geometry = ModuleType('foundation.seat_geometry')
        fusion = ModuleType('adsk.fusion')
        fusion.Design = SimpleNamespace(cast=lambda value: value)
        dialog.app.activeProduct = object()
        for identity in ('seat_face', 'seat_position'):
            dialog.fields[identity].selectionCount = 1
            dialog.fields[identity].selection = lambda index: SimpleNamespace(entity=object())
        dialog.fields['inner_relief_enabled'].value = True
        dialog.fields['inner_diameter_mm'].isValidExpression = False
        with patch.dict(sys.modules, {'foundation.seat_geometry': geometry, 'adsk.fusion': fusion}), \
                patch.object(sys.modules['adsk'], 'fusion', fusion, create=True):
            parameters = dialog._request(check_placement=False)[-1]
        self.assertEqual(parameters.shaft_mode, 'Off')
        self.assertFalse(parameters.inner_relief_enabled)
        dialog.fields['shaft_mode'].selectedItem.name = 'Through All'
        dialog._refresh_controls()
        self.assertFalse(dialog.fields['blind_depth_mm'].isEnabled)
        self.assertTrue(dialog.fields['inner_diameter_mm'].isEnabled)


if __name__ == '__main__':
    unittest.main()
