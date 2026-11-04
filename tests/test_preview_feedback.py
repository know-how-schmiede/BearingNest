"""Preview marker geometry and ownership; no native Fusion graphics acceptance."""
import importlib
import math
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1] / 'Fusion-Add-In/BearingNest'


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        package = ModuleType('feedback_test')
        package.__path__ = [str(ROOT)]
        self.lines = []
        self.group = NS(isValid=True, deleteMe=Mock(return_value=True))
        def add_lines(coordinates, indices, strip):
            line = NS(coordinates=coordinates, indices=indices, strip=strip)
            self.lines.append(line)
            return line
        self.group.addLines = Mock(side_effect=add_lines)
        self.design = NS(rootComponent=NS(customGraphicsGroups=NS(add=Mock(return_value=self.group))))
        core, fusion, adsk = ModuleType('adsk.core'), ModuleType('adsk.fusion'), ModuleType('adsk')
        core.Color = NS(create=lambda *args: args)
        fusion.CustomGraphicsCoordinates = NS(create=lambda data: data)
        fusion.CustomGraphicsSolidColorEffect = NS(create=lambda color: color)
        fusion.CustomGraphicsShowThroughColorEffect = NS(create=lambda color, opacity: (color, opacity))
        adsk.core, adsk.fusion = core, fusion
        self.modules = patch.dict(sys.modules, {'feedback_test': package, 'adsk': adsk,
            'adsk.core': core, 'adsk.fusion': fusion})
        self.modules.start()
        self.feedback = importlib.import_module('feedback_test.seat_feedback')
        self.graphics = importlib.import_module('feedback_test.preview_graphics').PreviewGraphics()

    def tearDown(self):
        self.modules.stop()

    def report(self):
        report = self.feedback.new_feedback()
        report['placements'] = {i: (NS(x=i*3, y=2, z=0), NS(x=0, y=0, z=1)) for i in (1, 2, 3)}
        report['issues'][1] = ['Breakout']
        report['warnings'][2] = ['Thin wall']
        return report

    def test_markers_follow_arbitrary_planes_and_use_explicit_cm_radius(self):
        center = (1, 2, 3)
        for normal in ((0, 0, 1), (0, 0, -1), (1, 0, 0), (1, 2, 3)):
            packed = self.feedback.marker_lines(center, normal, 1.2)
            points = [packed[i:i+3] for i in range(0, len(packed), 3)]
            for point in points:
                self.assertAlmostEqual(sum((point[i]-center[i])*normal[i] for i in range(3)), 0)
            for point in points[:-4]:
                self.assertAlmostEqual(math.dist(point, center), 1.2)
        for radius in (0, float('inf')):
            with self.assertRaises(ValueError):
                self.feedback.marker_lines(center, (0, 0, 1), radius)

    def test_invalid_warning_and_other_positions_have_red_amber_blue_nonselectable_markers(self):
        self.graphics.show(self.design, self.report(), 12)
        self.assertEqual([line.color for line in self.lines],
            [(230, 35, 35, 255), (230, 145, 0, 255), (35, 130, 230, 255)])
        for line in self.lines:
            self.assertFalse(line.isSelectable)
            self.assertEqual(line.weight, 3)
            self.assertEqual(line.showThrough[1], 0.8)
        self.graphics.clear()
        self.group.deleteMe.assert_called_once()
        self.assertIsNone(self.graphics.group)

    def test_no_graphics_are_created_for_an_empty_or_unlocatable_report(self):
        report = self.feedback.new_feedback()
        report['issues'][1] = ['Lost reference']
        self.graphics.show(self.design, report, 10)
        self.design.rootComponent.customGraphicsGroups.add.assert_not_called()

    def test_partial_graphics_failure_removes_owned_group(self):
        self.group.addLines.side_effect = [NS(), None]
        with self.assertRaises(RuntimeError):
            self.graphics.show(self.design, self.report(), 10)
        self.group.deleteMe.assert_called_once()
        self.assertIsNone(self.graphics.group)

    def test_failed_cleanup_retains_ownership_for_retry_and_blocks_new_groups(self):
        self.graphics.group = self.group
        self.group.deleteMe.return_value = False
        with self.assertRaises(RuntimeError):
            self.graphics.show(self.design, self.report(), 10)
        self.assertIs(self.graphics.group, self.group)
        self.design.rootComponent.customGraphicsGroups.add.assert_not_called()
        self.group.deleteMe.return_value = True
        self.graphics.clear()

    def test_transaction_already_removed_graphics_is_a_safe_cleanup(self):
        self.graphics.group = self.group
        self.group.isValid = False
        self.graphics.clear()
        self.group.deleteMe.assert_not_called()
        self.assertIsNone(self.graphics.group)
