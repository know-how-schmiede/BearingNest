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
        self.owner = None

    def itemById(self, identity):
        return next((field for field in self.fields if field.id == identity), None)

    def addTabCommandInput(self, identity, label):
        tab = SimpleNamespace(id=identity, label=label, children=Inputs())
        tab.children.owner = tab
        self.tabs.append(tab)
        return tab

    def addGroupCommandInput(self, identity, label):
        group = SimpleNamespace(id=identity, label=label, children=Inputs())
        group.children.owner = group
        self.fields.append(group)
        return group

    def addTableCommandInput(self, identity, label, columns, ratio):
        table = SimpleNamespace(id=identity, columnRatio=ratio, cells={}, rowCount=0)
        def add(field, row, column):
            table.cells[row, column] = field
            table.rowCount = max(table.rowCount, row + 1)
            return True
        table.addCommandInput = add
        self.fields.append(table)
        return table

    def addTextBoxCommandInput(self, identity, label, text, rows, readonly):
        field = SimpleNamespace(id=identity, text=text, readonly=readonly)
        self.fields.append(field)
        return field

    def addImageCommandInput(self, identity, label, filename):
        if not Path(filename).is_file():
            raise FileNotFoundError(filename)
        return SimpleNamespace()

    def addSelectionInput(self, identity, label, prompt):
        field = SimpleNamespace(id=identity, filters=[], selectionCount=0, entities=[])
        def selection(index):
            while len(field.entities) <= index:
                field.entities.append(object())
            return SimpleNamespace(entity=field.entities[index])
        def clear():
            field.entities.clear()
            field.selectionCount = 0
        def add(entity):
            field.entities.append(entity)
            field.selectionCount = len(field.entities)
            return True
        field.selection, field.clearSelection, field.addSelection = selection, clear, add
        field.addSelectionFilter = field.filters.append
        field.setSelectionLimits = lambda minimum, maximum: setattr(field, 'limits', (minimum, maximum))
        self.fields.append(field)
        return field

    def addValueInput(self, identity, label, units, expression):
        field = ValueField(identity, units, expression)
        field.parentCommandInput = self.owner
        field.name = label
        self.fields.append(field)
        return field

    def addDropDownCommandInput(self, identity, label, style):
        field = SimpleNamespace(id=identity, selectedItem=None, parentCommandInput=self.owner)
        items = []
        class ListItem:
            def __init__(self, name, selected):
                self.name = name
                self.isSelected = selected

            @property
            def isSelected(self):
                return field.selectedItem is self

            @isSelected.setter
            def isSelected(self, selected):
                if selected:
                    field.selectedItem = self
                elif field.selectedItem is self:
                    field.selectedItem = None

        def add(name, selected, icon):
            item = ListItem(name, selected)
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
        field = SimpleNamespace(id=identity, name=label, value=initial, parentCommandInput=self.owner)
        self.fields.append(field)
        return field

    def addBoolValueInput(self, identity, label, checkbox, resource, initial):
        field = SimpleNamespace(id=identity, name=label, value=initial, parentCommandInput=self.owner)
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
        self.custom_events, self.custom_queue = {}, []
        def register(identity):
            event = SimpleNamespace(eventId=identity)
            self.custom_events[identity] = event
            return event
        def fire(identity):
            self.custom_queue.append(identity)
            return True
        def unregister(identity):
            return self.custom_events.pop(identity, None) is not None
        self.app = SimpleNamespace(userInterface=self.ui, registerCustomEvent=register,
            fireCustomEvent=fire, unregisterCustomEvent=unregister)
        core.Application = SimpleNamespace(get=lambda: self.app)
        core.CommandCreatedEventArgs = object
        core.CommandEventArgs = object
        core.ValueInput = SimpleNamespace(createByString=lambda expression: expression)
        core.DropDownStyles = SimpleNamespace(TextListDropDownStyle=0)
        core.TablePresentationStyles = SimpleNamespace(transparentBackgroundTablePresentationStyle=2)
        adsk = ModuleType('adsk')
        adsk.core = core
        fusion = ModuleType('adsk.fusion')
        fusion.Design = SimpleNamespace(cast=lambda value: value)
        adsk.fusion = fusion
        self.callbacks = []

        def add_handler(event, callback, *, local_handlers):
            local_handlers.append(callback)
            self.callbacks.append(callback)
            if hasattr(event, 'eventId'):
                event.callback = callback

        utilities = ModuleType('foundation.lib.fusionAddInUtils')
        utilities.add_handler = add_handler
        package = ModuleType('foundation')
        package.__path__ = [str(ROOT)]
        commands = ModuleType('foundation.commands')
        commands.__path__ = [str(ROOT / 'commands')]
        self.modules = patch.dict(sys.modules, {
            'adsk': adsk, 'adsk.core': core, 'adsk.fusion': fusion, 'foundation': package,
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
        command = SimpleNamespace(commandInputs=inputs, destroy=object(), activate=object(),
                                  validateInputs=object(), inputChanged=object(),
                                  executePreview=object(), execute=object(),
                                  doExecutePreview=Mock(return_value=True),
                                  setDialogInitialSize=lambda width, height: None)
        with patch.object(self.entry.CatalogDialog.__init__.__globals__['model'], 'load',
                          side_effect=lambda: self.entry.CatalogDialog.__init__.__globals__['model'].defaults()):
            self.entry.command_created(SimpleNamespace(command=command))
        dialog = next(callback.__self__ for callback in reversed(self.callbacks)
                      if callback.__name__ == 'execute')
        return command, inputs, dialog

    def test_dialog_has_four_tabs_required_selections_and_handler_cleanup(self):
        command, inputs, dialog = self.make_dialog()
        self.assertEqual([tab.label for tab in inputs.tabs],
                         ['Bearing Seat', 'Bearing Catalog', 'Settings', 'Info'])
        self.assertTrue(command.isOKButtonVisible)
        self.assertEqual(command.okButtonText, 'Apply Seats')
        self.assertEqual(dialog.fields['seat_position'].limits, (1, 0))
        self.assertEqual(dialog.fields['seat_face'].filters, ['PlanarFaces'])
        self.assertIn('CircularEdges', dialog.fields['seat_position'].filters)
        self.assertTrue(dialog.fields['seat_preview'].value)
        self.assertTrue(self.entry.local_handlers)
        self.entry.command_destroy(None)
        self.assertFalse(self.entry.local_handlers)

    def test_only_dimensions_start_expanded_and_numeric_rows_reserve_label_space(self):
        _, inputs, dialog = self.make_dialog()
        def walk(children):
            for field in children.fields:
                yield field
                if hasattr(field, 'children'):
                    yield from walk(field.children)
        all_fields = [field for tab in inputs.tabs for field in walk(tab.children)]
        groups = [field for field in all_fields if hasattr(field, 'children')]
        self.assertEqual({field.id for field in groups if field.isExpanded},
                         {'seat_dimensions_group', 'bearing_dimensions_group'})
        rows = [field for field in all_fields if hasattr(field, 'cells')]
        numeric = [field for field in dialog.fields.values() if isinstance(field, ValueField)]
        self.assertLess(len(rows), len(numeric))
        self.assertEqual(sum(table.rowCount for table in rows), len(numeric) + 7)
        controls = {value.id for table in rows for (index, column), value in table.cells.items() if column == 1}
        self.assertTrue({'land_count', 'shaft_mode', 'seat_preview', 'inner_relief_enabled',
                         'edit_land_count', 'edit_shaft_mode', 'edit_inner_relief_enabled'} <= controls)
        for row in rows:
            self.assertEqual(row.columnRatio, '1:1')
            self.assertEqual((row.minimumVisibleRows, row.maximumVisibleRows), (row.rowCount, row.rowCount))
            for index in range(row.rowCount):
                caption, value = row.cells[index, 0], row.cells[index, 1]
                self.assertTrue(caption.isReadOnly)
                self.assertIs(dialog.fields[value.id], value)
                self.assertTrue(value.tooltipDescription)
                self.assertEqual(caption.tooltipDescription, value.tooltipDescription)
        # Opening groups manually is local to one command, not the next opening.
        next(field for field in groups if field.id == 'seat_fit_group').isExpanded = True
        _, reopened, _ = self.make_dialog()
        fit = next(field for field in reopened.tabs[0].children.fields if field.id == 'seat_fit_group')
        self.assertFalse(fit.isExpanded)

    def test_short_labels_keep_full_text_in_tooltips(self):
        _, inputs, dialog = self.make_dialog()
        self.assertEqual(dialog.fields['catalog_save'].name, 'Save to catalog')
        self.assertEqual(dialog.fields['catalog_save'].tooltip, 'Save parameters to bearing catalog')
        self.assertEqual(dialog.fields['profile_reset'].name, 'Reset')
        self.assertEqual(dialog.fields['profile_reset'].tooltip, 'Reset all three fields to suggested values')
        fields = inputs.tabs[1].children.fields
        dimensions = next(field for field in fields if field.id == 'bearing_dimensions_group')
        table = next(field for field in dimensions.children.fields if field.id == 'bearing_dimensions_group_values')
        index = next(index for (index, column), field in table.cells.items() if column == 1 and field.id == 'custom_inner_mm')
        self.assertEqual(table.cells[index, 0].value, 'Inner-ring diameter')
        self.assertEqual(table.cells[index, 0].tooltip, 'Drawing inner-ring outside diameter (0 = unknown)')

    def test_group_expansion_does_not_process_catalog_or_clear_preview_feedback(self):
        _, _, dialog = self.make_dialog()
        with patch.object(dialog, 'clear_feedback') as clear, \
                patch.object(dialog.catalog, 'process') as process, \
                patch.object(dialog, '_request') as request:
            self.change(dialog, 'seat_contour_group')
        clear.assert_not_called()
        process.assert_not_called()
        request.assert_not_called()

    def test_event_timing_is_buffered_until_close_and_keeps_only_recent_callbacks(self):
        _, _, dialog = self.make_dialog()
        dialog.app.log = Mock()
        for _ in range(40):
            self.change(dialog, 'seat_contour_group')
        dialog.app.log.assert_not_called()
        self.assertEqual(dialog.timing.stats['changed'][0], 40)
        self.assertEqual(len(dialog.timing.recent), 32)
        self.entry.command_destroy(None)
        dialog.app.log.assert_called_once()
        report = dialog.app.log.call_args.args[0]
        self.assertIn('count=40', report)
        self.assertIn('seat_contour_group', report)
        self.assertIn('native layout/rollback excluded', report)

    def test_event_timing_and_logging_failures_do_not_mask_callback_or_cleanup(self):
        _, _, dialog = self.make_dialog()
        dialog.timing.record = Mock(side_effect=RuntimeError('diagnostic failure'))
        self.change(dialog, 'seat_contour_group')
        dialog.timing.stats['changed'] = [1, 0.001, 0.001]
        dialog.app.log = Mock(side_effect=RuntimeError('logging unavailable'))
        self.entry.command_destroy(None)
        self.assertNotIn(dialog, self.entry._dialogs)

    def test_layout_preview_reuses_graphics_but_execute_always_rebuilds(self):
        _, _, dialog = self.make_dialog()
        cache = SimpleNamespace(clear=Mock(), show=Mock(),
            feedback={'placements': {}, 'warnings': {}, 'issues': {}})
        parameters = SimpleNamespace(contact_mm=21.9, depth_mm=7)
        request = (object(), SimpleNamespace(body=object()), [object()], parameters)
        def capture(cuts):
            dialog._cached_preview = cache
        with patch.object(dialog, '_request', return_value=request), \
                patch.object(dialog, '_apply', return_value=[]) as apply, \
                patch.object(dialog, '_capture_preview', side_effect=capture):
            dialog.preview(SimpleNamespace())
            self.change(dialog, 'seat_fit_group')
            args = SimpleNamespace(isValidResult=True)
            dialog.preview(args)
            self.change(dialog, 'seat_contour_group')
            dialog.preview(args)
            self.assertFalse(args.isValidResult)
            self.assertEqual(apply.call_count, 1)
            self.assertEqual(cache.show.call_count, 2)
            dialog.execute(SimpleNamespace())
            self.assertEqual(apply.call_count, 2)
            apply.assert_called_with(request, persist=True)

    def test_parameter_changes_and_reactivation_invalidate_cached_preview(self):
        _, _, dialog = self.make_dialog()
        cache = SimpleNamespace(clear=Mock())
        dialog._cached_preview, dialog._layout_preview = cache, True
        parameters = SimpleNamespace(contact_mm=21.9, depth_mm=7)
        with patch.object(dialog, '_request', return_value=(1, 2, [3], parameters)):
            self.change(dialog, 'outside_mm')
        cache.clear.assert_called_once()
        self.assertIsNone(dialog._cached_preview)
        self.assertFalse(dialog._layout_preview)
        dialog._cached_preview, dialog._layout_preview = cache, True
        dialog.activated(None)
        self.assertIsNone(dialog._cached_preview)
        self.assertFalse(dialog._layout_preview)

    def test_failed_cache_display_falls_back_to_full_preview(self):
        _, _, dialog = self.make_dialog()
        cache = SimpleNamespace(clear=Mock(), show=Mock(side_effect=RuntimeError('Unsupported')))
        dialog._cached_preview, dialog._layout_preview = cache, True
        parameters = SimpleNamespace(contact_mm=21.9, depth_mm=7)
        request = (1, SimpleNamespace(body=2), [3], parameters)
        with patch.object(dialog, '_request', return_value=request), \
                patch.object(dialog, '_apply', return_value=[]) as apply, \
                patch.object(dialog, '_capture_preview'):
            dialog.preview(SimpleNamespace())
        apply.assert_called_once_with(request, persist=False)
        self.assertIsNone(dialog.geometry_error)

    def test_existing_batch_preview_never_replays_cached_graphics(self):
        _, _, dialog = self.make_dialog()
        dialog._editing_records = [object()]
        cache = SimpleNamespace(clear=Mock(), show=Mock())
        dialog._cached_preview, dialog._layout_preview = cache, True
        parameters = SimpleNamespace(contact_mm=21.9, depth_mm=7)
        request = (1, None, dialog._editing_records, parameters)
        with patch.object(dialog, '_request', return_value=request), \
                patch.object(dialog, '_apply', return_value=[]) as apply:
            dialog.preview(SimpleNamespace())
        cache.show.assert_not_called()
        apply.assert_called_once_with(request, persist=False)

    def test_parameter_edit_requests_fusion_preview_without_reselecting_position(self):
        command, _, dialog = self.make_dialog()
        position = object()
        dialog.fields['seat_position'].selectionCount = 1
        old_cache = SimpleNamespace(clear=Mock(), show=Mock())
        dialog._cached_preview, dialog._layout_preview = old_cache, True
        parameters = SimpleNamespace(contact_mm=24.9, depth_mm=7)
        request = (1, SimpleNamespace(body=2), [position], parameters)
        def host_preview():
            # Model a synchronous callback plus a generated input notification.
            self.change(dialog, 'outside_mm')
            dialog.preview(SimpleNamespace())
            return True
        command.doExecutePreview.side_effect = host_preview
        dialog.fields['outside_mm'].expression = '25 mm'
        with patch.object(dialog, '_request', return_value=request), \
                patch.object(dialog, '_apply', return_value=[]) as apply, \
                patch.object(dialog, '_capture_preview'):
            self.change(dialog, 'outside_mm')
            command.doExecutePreview.assert_not_called()
            apply.assert_not_called()
            self.drain_preview_queue()
        command.doExecutePreview.assert_called_once()
        apply.assert_called_once_with(request, persist=False)
        old_cache.show.assert_not_called()
        old_cache.clear.assert_called_once()
        self.assertEqual(dialog.fields['seat_position'].selectionCount, 1)
        self.assertFalse(dialog._refreshing)
        self.assertIsNone(dialog.geometry_error)

    def test_table_options_and_preview_toggle_explicitly_refresh_geometry(self):
        command, _, dialog = self.make_dialog()
        parameters = SimpleNamespace(contact_mm=21.9, depth_mm=7)
        request = (1, SimpleNamespace(body=2), [object()], parameters)
        command.doExecutePreview.side_effect = lambda: dialog.preview(SimpleNamespace())
        with patch.object(dialog, '_request', return_value=request), \
                patch.object(dialog, '_apply', return_value=[]) as apply, \
                patch.object(dialog, '_capture_preview'):
            dialog.fields['shaft_mode'].selectedItem.name = 'Blind'
            self.change(dialog, 'shaft_mode')
            self.drain_preview_queue()
            self.assertEqual(apply.call_count, 1)
            dialog.fields['inner_relief_enabled'].value = True
            self.change(dialog, 'inner_relief_enabled')
            self.drain_preview_queue()
            self.assertEqual(apply.call_count, 2)
            dialog.fields['seat_preview'].value = False
            self.change(dialog, 'seat_preview')
            self.drain_preview_queue()
            self.assertEqual(apply.call_count, 2)
            dialog.fields['seat_preview'].value = True
            self.change(dialog, 'seat_preview')
            self.drain_preview_queue()
            self.assertEqual(apply.call_count, 3)
        self.assertEqual(command.doExecutePreview.call_count, 4)
        self.assertIsNone(dialog.geometry_error)

    def test_groups_validation_and_inactive_preview_do_not_force_rebuild(self):
        command, _, dialog = self.make_dialog()
        parameters = SimpleNamespace(contact_mm=21.9, depth_mm=7)
        with patch.object(dialog, '_request', return_value=(1, 2, [3], parameters)):
            self.change(dialog, 'seat_fit_group')
            dialog.validate(SimpleNamespace())
            dialog.fields['seat_preview'].value = False
            self.change(dialog, 'outside_mm')
        command.doExecutePreview.assert_not_called()

    def test_failed_explicit_preview_request_releases_reentrancy_guard(self):
        command, _, dialog = self.make_dialog()
        command.doExecutePreview.side_effect = RuntimeError('Preview request failed')
        dialog._refresh_preview('shaft_mode')
        self.drain_preview_queue()
        self.assertFalse(dialog._refreshing)
        self.assertEqual(dialog.geometry_error, 'Preview request failed')

    def test_idle_preview_restores_face_and_multiple_points_across_host_rollback(self):
        command, _, dialog = self.make_dialog()
        face = SimpleNamespace(isValid=True, entityToken='face')
        points = [SimpleNamespace(isValid=True, entityToken='point1'),
                  SimpleNamespace(isValid=True, entityToken='point2')]
        dialog.fields['seat_face'].addSelection(face)
        for point in points:
            dialog.fields['seat_position'].addSelection(point)
        replacements = {'face': [SimpleNamespace(isValid=True, entityToken='face')],
                        'point1': [SimpleNamespace(isValid=True, entityToken='point1')],
                        'point2': [SimpleNamespace(isValid=True, entityToken='point2')]}
        dialog.app.activeProduct = SimpleNamespace(findEntityByToken=lambda token: replacements[token])
        parameters = SimpleNamespace(contact_mm=21.9, depth_mm=7)
        observed = []
        def request(**kwargs):
            selected = [dialog.fields['seat_position'].selection(i).entity
                        for i in range(dialog.fields['seat_position'].selectionCount)]
            if command.doExecutePreview.call_count:
                self.assertEqual(selected, [replacements['point1'][0], replacements['point2'][0]])
                observed.append(selected)
            return (1, face, selected, parameters)
        def host_preview():
            dialog.fields['seat_face'].clearSelection()
            dialog.fields['seat_position'].clearSelection()
            face.isValid = False
            for point in points:
                point.isValid = False
            dialog.preview(SimpleNamespace())
            # Some hosts clear selection again while completing the forced call.
            dialog.fields['seat_position'].clearSelection()
            return True
        command.doExecutePreview.side_effect = host_preview
        with patch.object(dialog, '_request', side_effect=request), \
                patch.object(dialog, '_apply', return_value=[]) as apply, \
                patch.object(dialog, '_capture_preview'):
            self.change(dialog, 'shaft_mode')
            self.drain_preview_queue()
        self.assertEqual(len(observed), 1)
        self.assertEqual(dialog.fields['seat_face'].selectionCount, 1)
        self.assertEqual(dialog.fields['seat_position'].selectionCount, 2)
        apply.assert_called_once()
        self.assertIsNone(dialog.geometry_error)

    def test_manual_deselection_cancels_queued_restoration(self):
        command, _, dialog = self.make_dialog()
        dialog.fields['seat_position'].addSelection(object())
        parameters = SimpleNamespace(contact_mm=21.9, depth_mm=7)
        with patch.object(dialog, '_request', return_value=(1, 2, [3], parameters)):
            self.change(dialog, 'outside_mm')
            dialog.fields['seat_position'].clearSelection()
            self.change(dialog, 'seat_position')
            self.drain_preview_queue()
        command.doExecutePreview.assert_not_called()
        self.assertEqual(dialog.fields['seat_position'].selectionCount, 0)

    def test_duplicate_value_events_coalesce_and_native_preview_cancels_idle_request(self):
        command, _, dialog = self.make_dialog()
        parameters = SimpleNamespace(contact_mm=21.9, depth_mm=7)
        command.doExecutePreview.side_effect = lambda: dialog.preview(SimpleNamespace())
        with patch.object(dialog, '_request', return_value=(1, 2, [3], parameters)), \
                patch.object(dialog, '_apply', return_value=[]) as apply, \
                patch.object(dialog, '_capture_preview'):
            self.change(dialog, 'outside_mm')
            self.change(dialog, 'outside_mm')
            self.change(dialog, 'shaft_mode')
            self.assertEqual(len(self.custom_queue), 1)
            self.drain_preview_queue()
            command.doExecutePreview.assert_called_once()
            apply.assert_called_once()
            self.change(dialog, 'shaft_mode')
            dialog.preview(SimpleNamespace())  # Fusion already dispatched naturally.
            self.drain_preview_queue()
            command.doExecutePreview.assert_called_once()
            self.assertEqual(apply.call_count, 2)

    def test_destroy_disposes_queued_custom_event_without_rebuilding(self):
        command, _, dialog = self.make_dialog()
        dialog._refresh_preview('shaft_mode')
        self.assertTrue(self.custom_events)
        self.entry.command_destroy(None)
        self.assertFalse(self.custom_events)
        self.drain_preview_queue()
        command.doExecutePreview.assert_not_called()

    def test_selection_restore_rejects_ambiguous_tokens_without_partial_updates(self):
        _, _, dialog = self.make_dialog()
        face = SimpleNamespace(isValid=False, entityToken='face')
        point = SimpleNamespace(isValid=False, entityToken='point')
        dialog.app.activeProduct = SimpleNamespace(findEntityByToken=lambda token:
            [object()] if token == 'face' else [object(), object()])
        with self.assertRaises(ValueError):
            dialog._restore_selection({'seat_face': [(face, 'face')], 'seat_position': [(point, 'point')]})
        self.assertEqual(dialog.fields['seat_face'].selectionCount, 0)
        self.assertEqual(dialog.fields['seat_position'].selectionCount, 0)

    def test_retained_selection_is_not_resolved_again_against_preview_topology(self):
        _, _, dialog = self.make_dialog()
        point = SimpleNamespace(isValid=False, entityToken='original-edge')
        dialog.fields['seat_position'].addSelection(point)
        resolver = Mock(return_value=[])
        dialog.app.activeProduct = SimpleNamespace(findEntityByToken=resolver)
        dialog._restore_selection({'seat_position': [(point, 'original-edge')]})
        resolver.assert_not_called()
        self.assertEqual(dialog.fields['seat_position'].selectionCount, 1)

    def test_queued_preview_failure_releases_pending_state_for_retry(self):
        command, _, dialog = self.make_dialog()
        with patch.object(dialog.app, 'fireCustomEvent', side_effect=RuntimeError('Queue API failed')):
            dialog._refresh_preview('shaft_mode')
        self.assertFalse(dialog.preview_dispatch.pending)
        self.assertIn('Queue API failed', dialog.geometry_error)
        dialog._refresh_preview('shaft_mode')
        self.drain_preview_queue()
        command.doExecutePreview.assert_called_once()

    def test_false_enqueue_return_still_delivers_preview_like_native_fusion(self):
        command, _, dialog = self.make_dialog()
        enqueue = dialog.app.fireCustomEvent
        def native_false_return(identity):
            enqueue(identity)
            return False
        self.assertIs(dialog.preview_dispatch.event, self.custom_events[dialog.preview_dispatch.event_id])
        with patch.object(dialog.app, 'fireCustomEvent', side_effect=native_false_return):
            dialog._refresh_preview('shaft_mode')
        self.assertTrue(dialog.preview_dispatch.pending)
        self.assertIsNone(dialog.geometry_error)
        command.doExecutePreview.assert_not_called()
        self.drain_preview_queue()
        command.doExecutePreview.assert_called_once()
        self.assertFalse(dialog.preview_dispatch.pending)
        self.entry.command_destroy(None)
        self.assertIsNone(dialog.preview_dispatch.event)

    def test_preview_off_restores_source_face_token_not_temporary_cut_topology(self):
        command, _, dialog = self.make_dialog()
        face = SimpleNamespace(isValid=True, entityToken='source-face')
        point = SimpleNamespace(isValid=True, entityToken='source-point')
        restored_face = SimpleNamespace(isValid=True, entityToken='source-face')
        dialog.fields['seat_face'].addSelection(face)
        dialog.fields['seat_position'].addSelection(point)
        def resolve(token):
            if token == 'source-face':
                return [restored_face]
            if token == 'source-point':
                return [point]
            raise AssertionError('Temporary preview token must not be used after rollback')
        dialog.app.activeProduct = SimpleNamespace(findEntityByToken=resolve)
        parameters = SimpleNamespace(contact_mm=21.9, depth_mm=7)
        def request(**kwargs):
            return (dialog.app.activeProduct, dialog.fields['seat_face'].selection(0).entity,
                    [point], parameters)
        def build(request, **kwargs):
            # Model a selected face whose token changes when cut-preview features
            # modify its topology. The stored source token must remain unchanged.
            face.entityToken = 'temporary-preview-face'
            return []
        def rollback_and_preview():
            face.isValid = False
            dialog.fields['seat_face'].clearSelection()
            dialog.preview(SimpleNamespace())
            return True
        command.doExecutePreview.side_effect = rollback_and_preview
        with patch.object(dialog, '_request', side_effect=request), \
                patch.object(dialog, '_apply', side_effect=build) as apply, \
                patch.object(dialog, '_capture_preview'):
            dialog.preview(SimpleNamespace())
            self.assertEqual(dialog._selection_baseline['seat_face'][0][1], 'source-face')
            dialog.fields['seat_preview'].value = False
            self.change(dialog, 'seat_preview')
            self.drain_preview_queue()
        apply.assert_called_once()
        self.assertIs(dialog.fields['seat_face'].selection(0).entity, restored_face)
        self.assertEqual(dialog.fields['seat_position'].selectionCount, 1)
        self.assertFalse(dialog.fields['seat_preview'].value)
        self.assertIsNone(dialog.geometry_error)

    def test_explicit_face_replacement_discards_prior_source_token(self):
        _, _, dialog = self.make_dialog()
        old_face = SimpleNamespace(isValid=True, entityToken='old-face')
        new_face = SimpleNamespace(isValid=True, entityToken='new-face')
        dialog._selection_baseline['seat_face'] = [(old_face, 'old-face')]
        dialog.fields['seat_face'].addSelection(new_face)
        self.change(dialog, 'seat_face')
        self.assertEqual(dialog._capture_selection()['seat_face'][0][1], 'new-face')
        dialog.fields['seat_face'].clearSelection()
        self.change(dialog, 'seat_face')
        self.assertEqual(dialog._capture_selection()['seat_face'], [])

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

    def drain_preview_queue(self):
        for _ in range(50):
            if not self.custom_queue:
                return
            identity = self.custom_queue.pop(0)
            event = self.custom_events.get(identity)
            if event is not None:
                event.callback(SimpleNamespace())
        self.fail('Preview queue did not settle')

    def select_catalog_bearing(self, dialog, designation):
        label = next(label for label, record in dialog.catalog.bearing_choices.items()
                     if record and record.get('designation') == designation)
        dialog.fields['catalog_bearing'].selectedItem = SimpleNamespace(name=label)
        self.change(dialog, 'catalog_bearing')

    def test_dimension_only_catalog_selection_resets_previous_bearing_settings(self):
        _, _, dialog = self.make_dialog()
        dialog.fields['inner_diameter_mm'].expression = '9 mm'
        self.change(dialog, 'inner_diameter_mm')
        dialog.fields['correction_mm'].expression = '-0.2 mm'
        dialog.fields['relief_mm'].expression = '2 mm'
        self.select_catalog_bearing(dialog, '623')
        self.assertEqual(dialog.fields['bore_mm'].value, 0.3)
        self.assertEqual(dialog.fields['outside_mm'].value, 1)
        self.assertEqual(dialog.fields['width_mm'].value, 0.4)
        self.assertEqual(dialog.fields['correction_mm'].value, -0.01)
        self.assertEqual(dialog.fields['inner_diameter_mm'].value, 0.3)
        self.assertEqual(dialog.fields['relief_mm'].value, 0.12)
        self.assertTrue(dialog.fields['relief_mm_auto'].value)
        self.assertEqual(dialog.fields['catalog_save_name'].value, '623')
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
        self.assertIn('seat_preset', record)

    def test_catalog_selection_restores_every_saved_parameter_profile_and_metadata(self):
        _, _, dialog = self.make_dialog()
        catalog = dialog.catalog
        values = dict(outside_mm=24, width_mm=8, bore_mm=9, correction_mm=-0.15,
                      axial_mm=0.2, land_degrees=25, rotation_degrees=12,
                      relief_mm=1.3, fillet_mm=0.35, chamfer_mm=0.5,
                      shaft_allowance_mm=0.3, blind_depth_mm=15,
                      inner_diameter_mm=14, inner_depth_mm=0.5)
        parameters = dict(values, land_count=7, shaft_mode='Blind', inner_relief_enabled=True)
        profile = dict(catalog.profile, name='Stored printer', nozzle_mm=0.5)
        flags = dict(relief_mm_auto=False, fillet_mm_auto=True,
                     inner_depth_mm_auto=False, inner_diameter_auto=False)
        model = catalog._save.__globals__['model']
        record = dict(model.seed_bearings()[0], id='custom-full', designation='Complete preset',
                      d_mm=9, D_mm=24, B_mm=8, manufacturer='Example',
                      seat_preset=dict(parameters=parameters, profile=profile, auto_flags=flags))
        model.validate_bearing(record)
        catalog.data['bearings'].append(record)
        catalog._choices()
        self.select_catalog_bearing(dialog, 'Complete preset')
        for key, value in values.items():
            expected = math.radians(value) if key.endswith('degrees') else value / 10
            self.assertAlmostEqual(dialog.fields[key].value, expected, msg=key)
        for key, expected in (('land_count', '7'), ('shaft_mode', 'Blind')):
            items = dialog.fields[key].listItems
            self.assertTrue(next(items.item(i) for i in range(items.count)
                                 if items.item(i).name == expected).isSelected)
        self.assertTrue(dialog.fields['inner_relief_enabled'].value)
        self.assertEqual(catalog.profile, profile)
        for key in ('relief_mm_auto', 'fillet_mm_auto', 'inner_depth_mm_auto'):
            self.assertEqual(dialog.fields[key].value, flags[key])
        self.assertFalse(dialog._inner_diameter_auto)
        self.assertEqual(dialog.fields['profile_name'].value, 'Stored printer')
        self.assertEqual(dialog.fields['custom_manufacturer'].value, '')
        self.assertIsNone(catalog.editor_bearing)
        # Delayed programmatic selector/value events must not recalculate a preset.
        self.change(dialog, 'catalog_bearing')
        self.change(dialog, 'print_profile')
        self.change(dialog, 'fillet_mm')
        self.assertAlmostEqual(dialog.fields['fillet_mm'].value, 0.035)
        self.assertTrue(dialog.fields['fillet_mm_auto'].value)

    def test_compact_layout_and_named_parameter_catalog_round_trip(self):
        _, inputs, dialog = self.make_dialog()
        seat_ids = [field.id for field in inputs.tabs[0].children.fields]
        settings_ids = [field.id for field in inputs.tabs[2].children.fields]
        self.assertEqual(seat_ids[:3], ['seat_batch', 'catalog_search', 'catalog_bearing'])
        self.assertNotIn('foundation_status', seat_ids)
        self.assertNotIn('geometry_status', seat_ids)
        self.assertNotIn('profile_effective', seat_ids)
        self.assertIn('profiles_group', settings_ids)
        profile_group = next(field for field in inputs.tabs[0].children.fields if field.id == 'seat_profile_group')
        self.assertIn('print_profile', [field.id for field in profile_group.children.fields])
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

    def select_editor_bearing(self, dialog, designation):
        title = next(title for title, record in dialog.catalog.editor_choices.items()
                     if record and record['designation'] == designation)
        dialog.fields['catalog_editor'].selectedItem = SimpleNamespace(name=title)
        self.change(dialog, 'catalog_editor')

    def test_catalog_editor_updates_selected_entry_without_changing_active_seat(self):
        _, _, dialog = self.make_dialog()
        self.select_catalog_bearing(dialog, '608')
        catalog = dialog.catalog
        model = catalog._save.__globals__['model']
        self.select_editor_bearing(dialog, '623')
        self.assertEqual(dialog.fields['edit_outside_mm'].value, 1)
        self.assertFalse(dialog.fields['bearing_delete'].isEnabled)
        dialog.fields['custom_designation'].value = 'My 623'
        dialog.fields['edit_outside_mm'].expression = '11 mm'
        dialog.fields['edit_land_count'].listItems.item(2).isSelected = True
        dialog.fields['edit_correction_mm'].expression = '-0.15 mm'
        with patch.object(model, 'save'):
            catalog._action('bearing_save')
        record = catalog.data['bearings'][0]
        self.assertEqual(record['D_mm'], 11)
        self.assertEqual(record['seat_preset']['parameters']['land_count'], 7)
        self.assertEqual(record['seat_preset']['parameters']['correction_mm'], -0.15)
        self.assertEqual(catalog.bearing['designation'], '608')
        self.assertEqual(dialog.fields['outside_mm'].value, 2.2)
        self.assertTrue(dialog.fields['bearing_delete'].isEnabled)
        self.select_editor_bearing(dialog, 'My 623')
        dialog.fields['custom_manufacturer'].value = 'My manufacturer'
        with patch.object(model, 'save'):
            catalog._action('bearing_save')
        self.assertEqual(len(catalog.data['bearings']), 1)
        self.assertEqual(catalog.data['bearings'][0]['id'], record['id'])
        self.assertEqual(catalog.data['bearings'][0]['manufacturer'], 'My manufacturer')
        with patch.object(model, 'save'):
            catalog._action('bearing_delete')
        self.assertFalse(catalog.data['bearings'])
        self.assertEqual(catalog.bearing['designation'], '608')
        self.assertIsNone(catalog.editor_bearing)

    def test_catalog_editor_preserves_data_on_invalid_values_or_failed_save(self):
        _, _, dialog = self.make_dialog()
        catalog = dialog.catalog
        model = catalog._save.__globals__['model']
        self.select_editor_bearing(dialog, '623')
        original = catalog.editor_bearing.copy()
        dialog.fields['edit_width_mm'].expression = '0 mm'
        with patch.object(model, 'save') as save:
            with self.assertRaises(ValueError):
                catalog._action('bearing_save')
        save.assert_not_called()
        dialog.fields['edit_width_mm'].expression = '4 mm'
        with patch.object(model, 'save', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                catalog._action('bearing_save')
        self.assertFalse(catalog.data['bearings'])
        self.assertEqual(catalog.editor_bearing, original)
        with patch.object(model, 'save') as save:
            with self.assertRaises(ValueError):
                catalog._action('bearing_delete')
        save.assert_not_called()

    def test_settings_profile_inspection_does_not_change_active_seat(self):
        _, _, dialog = self.make_dialog()
        catalog = dialog.catalog
        model = catalog._save.__globals__['model']
        other = dict(model.DEFAULT_PROFILE, id='other', name='Other', nozzle_mm=0.6)
        catalog.data['profiles'].append(other)
        catalog._choices()
        title = next(title for title, record in catalog.management_choices.items() if record['id'] == 'other')
        dialog.fields['settings_profile'].selectedItem = SimpleNamespace(name=title)
        self.change(dialog, 'settings_profile')
        self.assertEqual(catalog.managed_profile, other)
        self.assertEqual(dialog.fields['profile_nozzle_mm'].value, 0.06)
        self.assertEqual(catalog.profile, model.DEFAULT_PROFILE)
        self.assertEqual(dialog.fields['relief_mm'].value, 0.12)

    def test_catalog_ring_dimension_replaces_automatic_placeholder_only(self):
        _, _, dialog = self.make_dialog()
        catalog = dialog.catalog
        model = catalog._save.__globals__['model']
        record = dict(model.seed_bearings()[-1], id='custom-ring', designation='Known ring',
                      inner_ring_outside_mm=12)
        catalog.data['bearings'].append(record)
        catalog._choices()
        self.select_catalog_bearing(dialog, 'Known ring')
        self.assertEqual(dialog.fields['inner_diameter_mm'].value, 1.2)
        self.assertFalse(dialog._inner_diameter_auto)
        dialog.fields['bore_mm'].expression = '9 mm'
        self.change(dialog, 'bore_mm')
        self.assertEqual(dialog.fields['inner_diameter_mm'].value, 1.2)
        dialog.fields['inner_diameter_mm'].expression = '13 mm'
        self.change(dialog, 'inner_diameter_mm')
        self.assertEqual(dialog.fields['inner_diameter_mm'].value, 1.3)
        self.assertNotIn('seat_preset', record)

    def test_catalog_ring_suggestion_preserves_manual_presets_and_historical_seats(self):
        _, _, dialog = self.make_dialog()
        catalog = dialog.catalog
        model = catalog._save.__globals__['model']
        record = dict(model.seed_bearings()[-1], inner_ring_outside_mm=12)
        automatic = catalog._preset(None)
        automatic['auto_flags']['inner_diameter_auto'] = True
        record['seat_preset'] = automatic
        proposed = catalog._preset(record)
        self.assertEqual(proposed['parameters']['inner_diameter_mm'], 12)
        self.assertEqual(automatic['parameters']['inner_diameter_mm'], 8)
        automatic['parameters']['inner_diameter_mm'] = 13
        automatic['auto_flags']['inner_diameter_auto'] = False
        self.assertEqual(catalog._preset(record)['parameters']['inner_diameter_mm'], 13)
        # Historical seat reopening uses its snapshot, not catalog suggestions.
        catalog.bearing = record
        automatic['parameters']['inner_diameter_mm'] = 8
        automatic['auto_flags']['inner_diameter_auto'] = True
        catalog._restore_preset(automatic)
        self.assertEqual(dialog.fields['inner_diameter_mm'].value, 0.8)
        self.assertTrue(dialog._inner_diameter_auto)

    def test_catalog_editor_bore_follow_and_manual_override_are_independent(self):
        _, _, dialog = self.make_dialog()
        self.select_editor_bearing(dialog, '608')
        dialog.fields['edit_bore_mm'].expression = '9 mm'
        self.change(dialog, 'edit_bore_mm')
        self.assertEqual(dialog.fields['edit_inner_diameter_mm'].value, 0.9)
        self.assertEqual(dialog.fields['bore_mm'].value, 0.8)
        dialog.fields['edit_inner_diameter_mm'].expression = '12 mm'
        self.change(dialog, 'edit_inner_diameter_mm')
        dialog.fields['edit_bore_mm'].expression = '10 mm'
        self.change(dialog, 'edit_bore_mm')
        self.assertEqual(dialog.fields['edit_inner_diameter_mm'].value, 1.2)
        self.assertFalse(dialog.catalog._editor_preset()['auto_flags']['inner_diameter_auto'])

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
        catalog._load_editor(record)
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
        self.assertTrue(dialog.fields['bore_mm'].isEnabled)
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
