"""Timeline grouping orchestration substitutes, not native Fusion acceptance."""
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch


class TimelineTests(unittest.TestCase):
    def setUp(self):
        package = ModuleType('timeline_test')
        package.__path__ = [str(Path(__file__).resolve().parents[1] / 'Fusion-Add-In/BearingNest')]
        self.modules = patch.dict(sys.modules, {'timeline_test': package})
        self.modules.start()
        self.module = importlib.import_module('timeline_test.timeline_batches')
        self.record = {'seat_id': '1234567890', 'features': {'contour': 's', 'seat_cut': 'c'}}
        self.result = NS(name='', isCollapsed=False)
        self.add = Mock(return_value=self.result)
        self.nodes = {'s': NS(timelineObject=NS(index=3, parentGroup=None)),
                      'c': NS(timelineObject=NS(index=4, parentGroup=None))}
        self.design = NS(timeline=NS(count=5, timelineGroups=NS(add=self.add)),
                         findEntityByToken=lambda token: [self.nodes[token]])
        self.load = patch.object(self.module.seat_storage, 'load', return_value=self.record)
        self.load.start()

    def tearDown(self):
        self.load.stop()
        self.modules.stop()

    def test_group_contains_exact_features_and_uses_dropdown_label(self):
        name = self.module.label([self.record], 2, 'Group {number}: {count} [{identity}]')
        self.module.group(self.design, ['cut'], name)
        self.add.assert_called_once_with(3, 4)
        self.assertEqual(self.result.name, 'Group 2: 1 [12345678]')
        self.assertTrue(self.result.isCollapsed)

    def test_foreign_interleaved_feature_prevents_grouping(self):
        self.nodes['s'].timelineObject.index = 2
        with self.assertRaisesRegex(RuntimeError, 'interleaved'):
            self.module.group(self.design, ['cut'], 'Name')
        self.add.assert_not_called()

    def test_failed_group_creation_aborts_execute(self):
        self.add.return_value = None
        with self.assertRaisesRegex(RuntimeError, 'could not create'):
            self.module.group(self.design, ['cut'], 'Name')
