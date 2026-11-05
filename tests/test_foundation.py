"""Isolated lifecycle checks; actual Fusion behavior requires manual checks."""
import importlib
import json
import math
from pathlib import Path
import sys
import tempfile
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


class ValueField:
    def __init__(self, identity, units, expression):
        self.id, self.units, self.isEnabled = identity, units, True
        self.expression = expression

    @property
    def expression(self):
        return self._expression

    @expression.setter
    def expression(self, expression):
        self._expression = expression
        try:
            number = float(expression.split()[0])
            self.value = math.radians(number) if self.units == 'deg' else number / 10 if self.units == 'mm' else number
            self.isValidExpression = True
        except ValueError:
            self.isValidExpression = False


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
        field = ValueField(identity, units, expression)
        self.fields.append(field)
        return field

    def addDropDownCommandInput(self, identity, label, style):
        field = SimpleNamespace(id=identity, selectedItem=None)
        items = []
        def add(name, selected, icon):
            item = SimpleNamespace(name=name, isSelected=selected)
            items.append(item)
            field.listItems.count = len(items)
            if selected:
                field.selectedItem = item
        def clear():
            items.clear()
            field.selectedItem = None
            field.listItems.count = 0
        field.listItems = SimpleNamespace(add=add, clear=clear, count=0, item=lambda index: items[index])
        self.fields.append(field)
        return field

    def addStringValueInput(self, identity, label, initial=''):
        field = SimpleNamespace(id=identity, value=initial)
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
        with patch.object(self.entry.CatalogDialog.__init__.__globals__['model'], 'load',
                          side_effect=lambda: self.entry.CatalogDialog.__init__.__globals__['model'].defaults()):
            self.entry.command_created(SimpleNamespace(command=command))
        dialog = next(callback.__self__ for callback in reversed(self.callbacks)
                      if callback.__name__ == 'execute')
        return command, inputs, dialog

    def test_dialog_has_three_tabs_required_selections_and_handler_cleanup(self):
        command, inputs, dialog = self.make_dialog()
        self.assertEqual([tab.label for tab in inputs.tabs],
                         ['Bearing Seat', 'Settings', 'About'])
        self.assertTrue(command.isOKButtonVisible)
        self.assertEqual(command.okButtonText, 'Apply Seats')
        self.assertEqual(dialog.fields['seat_position'].limits, (1, 0))
        self.assertEqual(dialog.fields['seat_face'].filters, ['PlanarFaces'])
        self.assertIn('CircularEdges', dialog.fields['seat_position'].filters)
        self.assertTrue(dialog.fields['seat_preview'].value)
        self.assertTrue(self.entry.local_handlers)
        self.entry.command_destroy(None)
        self.assertFalse(self.entry.local_handlers)

    def test_execute_failure_marks_entire_command_transaction_for_abort(self):
        command, inputs, dialog = self.make_dialog()
        dialog.catalog = None
        geometry = ModuleType('foundation.seat_geometry')
        geometry.create_seats = Mock(side_effect=RuntimeError('snapshot failed'))
        args = SimpleNamespace()
        with patch.dict(sys.modules, {'foundation.seat_geometry': geometry}), \
                patch.object(dialog, '_request', return_value=(1, 2, 3, 4)):
            dialog.execute(args)
        self.assertTrue(args.executeFailed)
        self.assertEqual(args.executeFailedMessage, 'snapshot failed')

    def change(self, dialog, identity):
        dialog.changed(SimpleNamespace(input=SimpleNamespace(id=identity)))

    def select_catalog_bearing(self, dialog, designation):
        label = next(label for label, record in dialog.catalog.bearing_choices.items()
                     if record and record.get('designation') == designation)
        dialog.fields['catalog_bearing'].selectedItem = SimpleNamespace(name=label)
        self.change(dialog, 'catalog_bearing')

    def test_catalog_selection_updates_dimensions_but_keeps_fit_and_manual_relief(self):
        _, _, dialog = self.make_dialog()
        dialog.fields['inner_diameter_mm'].expression = '9 mm'
        self.change(dialog, 'inner_diameter_mm')
        self.select_catalog_bearing(dialog, '623')
        self.assertEqual(dialog.fields['bore_mm'].value, 0.3)
        self.assertEqual(dialog.fields['outside_mm'].value, 1)
        self.assertEqual(dialog.fields['width_mm'].value, 0.4)
        self.assertEqual(dialog.fields['correction_mm'].value, -0.01)
        self.assertEqual(dialog.fields['inner_diameter_mm'].value, 0.9)
        self.assertIsNone(dialog.catalog.bearing['inner_ring_outside_mm'])

    def test_profile_save_switch_preserves_manual_field_and_reset_restores_auto(self):
        _, _, dialog = self.make_dialog()
        catalog = dialog.catalog
        dialog.fields['relief_mm'].expression = '1.5 mm'
        self.change(dialog, 'relief_mm')
        self.assertFalse(dialog.fields['relief_mm_auto'].value)
        dialog.fields['profile_name'].value = 'Coarse'
        dialog.fields['profile_nozzle_mm'].expression = '0.6 mm'
        dialog.fields['profile_layer_mm'].expression = '0.3 mm'
        dialog.fields['profile_save'].value = True
        with patch.object(catalog._save.__globals__['model'], 'save') as save:
            self.change(dialog, 'profile_save')
        save.assert_called_once()
        self.assertEqual(catalog.profile['name'], 'Coarse')
        self.assertAlmostEqual(dialog.fields['relief_mm'].value, 0.15)
        self.assertAlmostEqual(dialog.fields['fillet_mm'].value, 0.06)
        self.assertAlmostEqual(dialog.fields['inner_depth_mm'].value, 0.06)
        self.assertEqual(catalog.profile['relief_factor'], 3)
        dialog.fields['profile_reset'].value = True
        self.change(dialog, 'profile_reset')
        self.assertAlmostEqual(dialog.fields['relief_mm'].value, 0.18)
        self.assertTrue(dialog.fields['relief_mm_auto'].value)
        # A delayed event for a programmatic assignment must keep Auto enabled.
        self.change(dialog, 'relief_mm')
        self.assertTrue(dialog.fields['relief_mm_auto'].value)

    def test_catalog_search_does_not_change_the_current_dimensions(self):
        _, _, dialog = self.make_dialog()
        self.select_catalog_bearing(dialog, '608')
        dialog.fields['catalog_search'].value = 'not found'
        self.change(dialog, 'catalog_search')
        self.assertEqual(dialog.catalog.bearing['designation'], '608')
        self.assertEqual(dialog.fields['outside_mm'].value, 2.2)
        self.assertEqual(len(dialog.catalog.bearing_choices), 2)  # manual + current snapshot

    def test_custom_bearing_save_round_trips_unknown_ring_and_metadata(self):
        _, _, dialog = self.make_dialog()
        catalog = dialog.catalog
        dialog.fields['custom_designation'].value = 'My bearing'
        dialog.fields['custom_source'].value = 'My drawing'
        dialog.fields['custom_purchasing_url'].value = 'https://example.com/item'
        dialog.fields['bearing_save'].value = True
        with patch.object(catalog._save.__globals__['model'], 'save') as save:
            self.change(dialog, 'bearing_save')
        save.assert_called_once()
        record = catalog.data['bearings'][0]
        self.assertEqual(record['D_mm'], 22)
        self.assertEqual(record['source'], 'My drawing')
        self.assertIsNone(record['inner_ring_outside_mm'])
        self.assertTrue(record['id'].startswith('custom-'))
        self.assertFalse(dialog.fields['bearing_save'].value)

    def test_compact_layout_and_named_parameter_catalog_round_trip(self):
        _, inputs, dialog = self.make_dialog()
        seat_ids = [field.id for field in inputs.tabs[0].children.fields]
        settings_ids = [field.id for field in inputs.tabs[1].children.fields]
        self.assertEqual(seat_ids[:3], ['seat_batch', 'catalog_search', 'catalog_bearing'])
        self.assertNotIn('foundation_status', seat_ids)
        self.assertNotIn('geometry_status', seat_ids)
        self.assertNotIn('profile_effective', seat_ids)
        self.assertIn('print_profile', settings_ids)
        self.assertNotIn('print_profile', seat_ids)
        self.assertLess(seat_ids.index('seat_status'), seat_ids.index('catalog_save_name'))
        self.assertEqual(seat_ids[seat_ids.index('catalog_save_name') + 1], 'catalog_save')
        self.assertAlmostEqual(dialog.fields['chamfer_mm'].value, 0.04)
        dialog.fields['catalog_save_name'].value = '608 printed seat'
        dialog.fields['land_count'].selectedItem.name = '7'
        dialog.fields['land_degrees'].expression = '25 deg'
        dialog.fields['correction_mm'].expression = '-0.15 mm'
        model = dialog.catalog._save.__globals__['model']
        with patch.object(model, 'save') as save:
            dialog.fields['catalog_save'].value = True
            self.change(dialog, 'catalog_save')
        save.assert_called_once()
        record = dialog.catalog.data['bearings'][0]
        model.validate_bearing(record)
        self.assertEqual(record['designation'], '608 printed seat')
        self.assertEqual(record['seat_preset']['parameters']['land_count'], 7)
        self.assertEqual(record['seat_preset']['parameters']['land_degrees'], 25)
        dialog.fields['correction_mm'].expression = '0 mm'
        dialog.catalog._restore_preset(record['seat_preset'])
        self.assertAlmostEqual(dialog.fields['correction_mm'].value, -0.015)
        self.assertFalse(dialog.fields['catalog_save'].value)

    def test_named_catalog_save_rejects_missing_name_and_failed_storage(self):
        _, _, dialog = self.make_dialog()
        model = dialog.catalog._save.__globals__['model']
        with patch.object(model, 'save') as save:
            with self.assertRaises(ValueError):
                dialog.catalog._save_parameters()
        save.assert_not_called()
        dialog.fields['catalog_save_name'].value = 'Example'
        with patch.object(model, 'save', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                dialog.catalog._save_parameters()
        self.assertEqual(dialog.catalog.data['bearings'], [])

    def test_invalid_settings_do_not_partially_replace_data_or_profile(self):
        _, _, dialog = self.make_dialog()
        original = dialog.catalog.profile.copy()
        dialog.fields['profile_nozzle_mm'].expression = '0 mm'
        dialog.fields['profile_save'].value = True
        with patch.object(dialog.catalog._save.__globals__['model'], 'save') as save:
            self.change(dialog, 'profile_save')
        save.assert_not_called()
        self.assertEqual(dialog.catalog.profile, original)
        self.assertIn('positive', dialog.catalog.status.formattedText)

    def test_restoring_a_snapshot_keeps_old_values_and_profile_despite_library_changes(self):
        _, _, dialog = self.make_dialog()
        model = dialog.catalog._save.__globals__['model']
        stored_profile = dict(model.DEFAULT_PROFILE, nozzle_mm=0.25, name='Historical')
        record = {'bearing': model.seed_bearings()[-1], 'profile': stored_profile,
                  'auto_flags': {'relief_mm_auto': True}}
        dialog.fields['relief_mm'].expression = '0.8 mm'
        dialog.catalog.data['profiles'][0]['nozzle_mm'] = 1
        dialog.catalog.restore(record)
        self.assertEqual(dialog.fields['relief_mm'].value, 0.08)
        self.assertEqual(dialog.catalog.profile['nozzle_mm'], 0.25)
        self.assertTrue(dialog.fields['relief_mm_auto'].value)
        self.assertFalse(dialog.fields['fillet_mm_auto'].value)
        self.assertIn('Stored seat profile snapshot', dialog.catalog.profile_choices)

    def test_persistent_creation_passes_effective_bearing_profile_and_flags(self):
        _, _, dialog = self.make_dialog()
        self.select_catalog_bearing(dialog, '608')
        values = self.entry.SeatDialog.__init__.__globals__['SeatParameters'](outside_mm=23)
        geometry = ModuleType('foundation.seat_geometry')
        geometry.create_seats = Mock()
        with patch.dict(sys.modules, {'foundation.seat_geometry': geometry}):
            dialog._apply((1, 2, [3], values), persist=True)
        options = geometry.create_seats.call_args.kwargs
        self.assertEqual(options['bearing']['D_mm'], 23)
        self.assertTrue(options['bearing']['dimensions_overridden'])
        self.assertEqual(options['profile']['nozzle_mm'], 0.4)
        self.assertTrue(options['auto_flags']['relief_mm_auto'])

    def test_delayed_selector_events_after_restore_do_not_reapply_library_defaults(self):
        _, _, dialog = self.make_dialog()
        model = dialog.catalog._save.__globals__['model']
        dialog.fields['relief_mm'].expression = '1.7 mm'
        dialog.fields['outside_mm'].expression = '23 mm'
        bearing = dict(model.seed_bearings()[-1], D_mm=23)
        dialog.catalog.restore({'bearing': bearing, 'profile': dict(model.DEFAULT_PROFILE),
                                'auto_flags': {'relief_mm_auto': True}})
        self.change(dialog, 'print_profile')
        self.change(dialog, 'catalog_bearing')
        self.change(dialog, 'relief_mm_auto')
        self.change(dialog, 'fillet_mm_auto')
        self.assertAlmostEqual(dialog.fields['relief_mm'].value, 0.17)
        self.assertEqual(dialog.fields['outside_mm'].value, 2.3)
        dialog.fields['fillet_mm_auto'].value = True
        self.change(dialog, 'fillet_mm_auto')
        self.assertAlmostEqual(dialog.fields['relief_mm'].value, 0.17)
        # The current library size remains an explicit alternative to the snapshot.
        self.select_catalog_bearing(dialog, '608')
        self.assertEqual(dialog.fields['outside_mm'].value, 2.2)

    def test_import_is_atomic_and_does_not_modify_current_seat_profile(self):
        _, _, dialog = self.make_dialog()
        catalog = dialog.catalog
        model = catalog._save.__globals__['model']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'import.json'
            imported = model.defaults()
            imported['profiles'][0]['nozzle_mm'] = 0.8
            model.save(imported, path)
            dialog.fields['settings_file'].value = str(path)
            with patch.object(model, 'save') as save:
                catalog._action('settings_import')
            save.assert_called_once()
            self.assertEqual(catalog.data['profiles'][0]['nozzle_mm'], 0.8)
            self.assertEqual(catalog.profile['nozzle_mm'], 0.4)
            self.assertAlmostEqual(dialog.fields['relief_mm'].value, 0.12)
            before = catalog.data.copy()
            path.write_text('{"schema_version":999}')
            with patch.object(model, 'save') as save:
                with self.assertRaises(ValueError):
                    catalog._action('settings_import')
            save.assert_not_called()
            self.assertEqual(catalog.data, before)

    def test_export_does_not_overwrite_existing_files(self):
        _, _, dialog = self.make_dialog()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'export.json'
            dialog.fields['settings_file'].value = str(path)
            dialog.catalog._action('settings_export')
            content = path.read_bytes()
            with self.assertRaises(ValueError):
                dialog.catalog._action('settings_export')
            self.assertEqual(path.read_bytes(), content)

    def test_corrupt_settings_block_save_and_last_profile_cannot_be_deleted(self):
        _, _, dialog = self.make_dialog()
        catalog = dialog.catalog
        model = catalog._save.__globals__['model']
        with patch.object(model, 'save') as save:
            catalog.load_error = 'Corrupt original'
            with self.assertRaises(ValueError):
                catalog._save(model.defaults())
            catalog.load_error = None
            # A real validation failure occurs before reaching file replacement.
            with self.assertRaises(ValueError):
                model.validate(dict(catalog.data, profiles=[]))
        save.assert_not_called()

    def test_deleting_library_entries_keeps_active_seat_snapshots(self):
        _, _, dialog = self.make_dialog()
        catalog = dialog.catalog
        model = catalog._save.__globals__['model']
        record = dict(model.seed_bearings()[-1], id='custom-test')
        catalog.data['bearings'].append(record.copy())
        catalog.bearing = record.copy()
        catalog.data['profiles'].append(dict(model.DEFAULT_PROFILE, id='other', name='Other', nozzle_mm=0.6))
        original_profile = catalog.profile.copy()
        dialog.fields['custom_id'].value = 'custom-test'
        with patch.object(model, 'save'):
            catalog._action('bearing_delete')
            catalog._action('profile_delete')
        self.assertEqual(catalog.bearing, record)
        self.assertEqual(catalog.profile, original_profile)
        self.assertAlmostEqual(dialog.fields['relief_mm'].value, 0.12)
        self.assertFalse(catalog.data['bearings'])
        self.assertEqual(catalog.data['profiles'][0]['name'], 'Other')
        self.assertIn('Stored seat profile snapshot', catalog.profile_choices)

    def test_saved_batch_refills_parameters_without_required_hidden_selections(self):
        command, inputs, dialog = self.make_dialog()
        values = self.entry.SeatDialog.__init__.__globals__['SeatParameters'](
            outside_mm=24, chamfer_mm=0.3, inner_diameter_mm=12)
        record = {'parameters': values.snapshot_values(), 'auto_flags': {'inner_diameter_auto': False}}
        dialog._batches['saved'] = [record]
        dialog.fields['seat_batch'].selectedItem.name = 'saved'
        edit = ModuleType('foundation.seat_edit')
        edit.parameters = Mock(return_value=values)
        with patch.dict(sys.modules, {'foundation.seat_edit': edit}):
            dialog.changed(SimpleNamespace(input=SimpleNamespace(id='seat_batch')))
        self.assertEqual(dialog.fields['outside_mm'].value, 2.4)
        self.assertEqual(dialog.fields['chamfer_mm'].value, 0.03)
        self.assertFalse(dialog._inner_diameter_auto)
        self.assertFalse(dialog.fields['seat_face'].isVisible)
        self.assertEqual(dialog.fields['seat_position'].limits, (0, 0))
        self.assertIs(dialog._editing_records[0], record)
        dialog.fields['seat_batch'].selectedItem.name = 'Create new seats'
        dialog.changed(SimpleNamespace(input=SimpleNamespace(id='seat_batch')))
        self.assertIsNone(dialog._editing_records)
        self.assertTrue(dialog.fields['seat_face'].isVisible)
        self.assertEqual(dialog.fields['seat_position'].limits, (1, 0))

    def test_edit_execute_failure_aborts_transaction_and_routes_to_update(self):
        command, inputs, dialog = self.make_dialog()
        dialog.catalog = None
        dialog._editing_records = [{'seat_id': 'saved'}]
        edit = ModuleType('foundation.seat_edit')
        edit.update = Mock(side_effect=RuntimeError('edit failure'))
        geometry = ModuleType('foundation.seat_geometry')
        args = SimpleNamespace()
        with patch.dict(sys.modules, {'foundation.seat_edit': edit, 'foundation.seat_geometry': geometry}), \
                patch.object(dialog, '_request', return_value=(1, None, dialog._editing_records, 4)):
            dialog.execute(args)
        self.assertTrue(args.executeFailed)
        self.assertEqual(args.executeFailedMessage, 'edit failure')
        edit.update.assert_called_once_with(1, dialog._editing_records, 4, persist=True,
            auto_flags={'inner_diameter_auto': True}, feedback=dialog.feedback)

    def test_preview_is_on_by_default_can_be_disabled_and_requires_execute(self):
        command, inputs, dialog = self.make_dialog()
        geometry = ModuleType('foundation.seat_geometry')
        geometry.create_seats = Mock()
        args = SimpleNamespace(isValidResult=True)
        parameters = SimpleNamespace(contact_mm=21.9, depth_mm=7)
        with patch.dict(sys.modules, {'foundation.seat_geometry': geometry}), \
                patch.object(dialog, '_request', return_value=(1, 2, [3], parameters)):
            dialog.fields['seat_preview'].value = False
            dialog.preview(args)
            geometry.create_seats.assert_not_called()
            dialog.fields['seat_preview'].value = True
            dialog.preview(args)
        self.assertFalse(args.isValidResult)
        geometry.create_seats.assert_called_once_with(1, 2, [3], parameters, persist=False,
            feedback=dialog.feedback, wall_threshold_mm=0.8)

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

    def test_wall_warning_preview_remains_valid_and_draws_advisory_markers(self):
        _, _, dialog = self.make_dialog()
        dialog._graphics = Mock()
        parameters = SimpleNamespace(contact_mm=21.9, depth_mm=7, relief_mm=1.2, chamfer_mm=0)
        geometry = ModuleType('foundation.seat_geometry')
        def create(*args, **kwargs):
            kwargs['feedback']['warnings'][1] = ['Possible thin wall; creation allowed.']
        geometry.create_seats = Mock(side_effect=create)
        with patch.dict(sys.modules, {'foundation.seat_geometry': geometry}), \
                patch.object(dialog, '_request', return_value=(1, 2, [3], parameters)):
            dialog.preview(SimpleNamespace())
            validation = SimpleNamespace(areInputsValid=False)
            dialog.validate(validation)
        self.assertTrue(validation.areInputsValid)
        self.assertIsNone(dialog.geometry_error)
        self.assertIn('Advisory wall warnings', dialog.status.formattedText)
        dialog._graphics.show.assert_called_once()
        self.assertEqual(dialog._graphics.show.call_args.args[:2], (1, dialog.feedback))
        self.assertAlmostEqual(dialog._graphics.show.call_args.args[2], 12.15)

    def test_invalid_preview_blocks_batch_and_clears_markers_on_correction(self):
        _, _, dialog = self.make_dialog()
        dialog._graphics = Mock()
        parameters = SimpleNamespace(contact_mm=21.9, depth_mm=7, relief_mm=1.2, chamfer_mm=0)
        geometry = ModuleType('foundation.seat_geometry')
        def create(*args, **kwargs):
            kwargs['feedback']['issues'][2] = ['Position 2: breakout']
            raise ValueError('Position 2: breakout')
        geometry.create_seats = Mock(side_effect=create)
        with patch.dict(sys.modules, {'foundation.seat_geometry': geometry}), \
                patch.object(dialog, '_request', return_value=(1, 2, [3, 4], parameters)):
            dialog.preview(SimpleNamespace())
            validation = SimpleNamespace(areInputsValid=True)
            dialog.validate(validation)
            self.assertFalse(validation.areInputsValid)
            self.assertIn('Position 2', dialog.status.formattedText)
            dialog._graphics.show.assert_called_once()
            self.change(dialog, 'rotation_degrees')
        self.assertIsNone(dialog.geometry_error)
        self.assertFalse(dialog.feedback['issues'])
        self.assertEqual(dialog._graphics.clear.call_count, 2)

    def test_disabling_preview_removes_markers_without_touching_the_model(self):
        _, _, dialog = self.make_dialog()
        dialog._graphics = Mock()
        dialog.feedback['issues'][1] = ['Old error']
        dialog.fields['seat_preview'].value = False
        with patch.object(dialog, '_request') as request:
            dialog.preview(SimpleNamespace())
        request.assert_not_called()
        dialog._graphics.clear.assert_called_once()
        self.assertFalse(dialog.feedback['issues'])

    def test_marker_rendering_failure_keeps_warning_only_geometry_valid(self):
        _, _, dialog = self.make_dialog()
        dialog._graphics = Mock()
        dialog._graphics.show.side_effect = RuntimeError('Graphics not available')
        parameters = SimpleNamespace(contact_mm=21.9, depth_mm=7, relief_mm=1.2, chamfer_mm=0)
        geometry = ModuleType('foundation.seat_geometry')
        def create(*args, **kwargs):
            kwargs['feedback']['warnings'][1] = ['Possible wall warning']
        geometry.create_seats = Mock(side_effect=create)
        with patch.dict(sys.modules, {'foundation.seat_geometry': geometry}), \
                patch.object(dialog, '_request', return_value=(1, 2, [3], parameters)):
            dialog.preview(SimpleNamespace())
            validation = SimpleNamespace(areInputsValid=False)
            dialog.validate(validation)
        self.assertTrue(validation.areInputsValid)
        self.assertIn('Preview markers unavailable', dialog.status.formattedText)
        self.assertIn('Possible wall warning', dialog.status.formattedText)

    def test_destroy_and_stop_release_owned_preview_graphics(self):
        for close in (self.entry.command_destroy, lambda args: self.entry.stop()):
            _, _, dialog = self.make_dialog()
            dialog._graphics = Mock()
            close(None)
            dialog._graphics.clear.assert_called_once()
            self.assertFalse(self.entry._dialogs)

    def test_graphics_cleanup_failure_is_retained_for_retry(self):
        _, _, dialog = self.make_dialog()
        dialog._graphics = Mock()
        dialog._graphics.clear.side_effect = RuntimeError('Marker cleanup failed')
        with self.assertRaisesRegex(RuntimeError, 'Marker cleanup failed'):
            self.entry.command_destroy(None)
        self.assertIn(dialog, self.entry._dialogs)
        dialog._graphics.clear.side_effect = None
        self.entry.command_destroy(None)
        self.assertFalse(self.entry._dialogs)

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

    def test_inner_diameter_follows_bore_until_manual_override(self):
        command, inputs, dialog = self.make_dialog()
        self.assertEqual(dialog.fields['inner_diameter_mm'].value, 0.8)
        dialog.fields['bore_mm'].expression = '10 mm'
        dialog.changed(SimpleNamespace(input=SimpleNamespace(id='bore_mm')))
        self.assertEqual(dialog.fields['inner_diameter_mm'].value, 1.0)
        dialog.fields['inner_diameter_mm'].expression = '12 mm'
        dialog.changed(SimpleNamespace(input=SimpleNamespace(id='inner_diameter_mm')))
        dialog.fields['bore_mm'].expression = '11 mm'
        dialog.changed(SimpleNamespace(input=SimpleNamespace(id='bore_mm')))
        self.assertEqual(dialog.fields['inner_diameter_mm'].value, 1.2)

    def test_face_selection_moves_focus_to_positions_without_later_focus_theft(self):
        command, inputs, dialog = self.make_dialog()
        dialog.fields['seat_face'].selectionCount = 1
        dialog.changed(SimpleNamespace(input=SimpleNamespace(id='seat_face')))
        self.assertTrue(dialog.fields['seat_position'].hasFocus)
        dialog.fields['seat_position'].hasFocus = False
        dialog.changed(SimpleNamespace(input=SimpleNamespace(id='outside_mm')))
        self.assertFalse(dialog.fields['seat_position'].hasFocus)

    def test_hidden_position_selector_is_not_focused(self):
        command, inputs, dialog = self.make_dialog()
        dialog.fields['seat_face'].selectionCount = 1
        dialog.fields['seat_position'].isVisible = False
        dialog.fields['seat_position'].hasFocus = False
        dialog.changed(SimpleNamespace(input=SimpleNamespace(id='seat_face')))
        self.assertFalse(dialog.fields['seat_position'].hasFocus)

    def test_delayed_auto_fill_change_event_does_not_turn_the_preset_into_manual_override(self):
        command, inputs, dialog = self.make_dialog()
        dialog.fields['bore_mm'].expression = '10 mm'
        dialog.changed(SimpleNamespace(input=SimpleNamespace(id='bore_mm')))
        dialog.changed(SimpleNamespace(input=SimpleNamespace(id='inner_diameter_mm')))
        dialog.fields['bore_mm'].expression = '11 mm'
        dialog.changed(SimpleNamespace(input=SimpleNamespace(id='bore_mm')))
        self.assertEqual(dialog.fields['inner_diameter_mm'].value, 1.1)


if __name__ == '__main__':
    unittest.main()
