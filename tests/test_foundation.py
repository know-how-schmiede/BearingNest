"""Isolated lifecycle checks; actual Fusion behavior requires manual checks."""
import importlib
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

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
        return self.add(identity, id=identity, commandCreated=object())

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

    def test_dialog_has_three_tabs_and_close_only_with_handler_cleanup(self):
        inputs = Inputs()
        command = SimpleNamespace(commandInputs=inputs, destroy=object(),
                                  setDialogInitialSize=lambda width, height: None)
        self.entry.command_created(SimpleNamespace(command=command))
        self.assertEqual([tab.label for tab in inputs.tabs],
                         ['Bearing Seat', 'Settings', 'About'])
        self.assertFalse(command.isOKButtonVisible)
        for tab in inputs.tabs:
            self.assertTrue(all(field.readonly for field in tab.children.fields))
        self.assertTrue(self.entry.local_handlers)
        self.entry.command_destroy(None)
        self.assertFalse(self.entry.local_handlers)

    def test_manifest_and_runtime_versions_match(self):
        manifest = json.loads((ROOT / 'BearingNest.manifest').read_text(encoding='utf-8-sig'))
        self.assertEqual(manifest['version'], self.entry.VERSION)
        self.assertTrue((ROOT / manifest['iconFilename']).is_file())


if __name__ == '__main__':
    unittest.main()
