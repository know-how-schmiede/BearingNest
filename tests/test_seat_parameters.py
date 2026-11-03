"""Physical parameter conventions and the shared contour's arc interpretation."""
import importlib
import math
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / 'Fusion-Add-In/BearingNest'


class ParameterTests(unittest.TestCase):
    def setUp(self):
        package = ModuleType('parameter_test')
        package.__path__ = [str(ROOT)]
        self.modules = patch.dict(sys.modules, {'parameter_test': package})
        self.modules.start()
        self.model = importlib.import_module('parameter_test.seat_parameters')

    def tearDown(self):
        self.modules.stop()

    def test_correction_signs_and_explicit_mm_conversion(self):
        parameters = self.model.SeatParameters(correction_mm=-0.2, axial_mm=0.5)
        self.assertEqual(parameters.contact_mm, 21.8)
        self.assertEqual(parameters.depth_mm, 7.5)
        self.assertEqual(self.model.mm_to_cm(7.5), 0.75)
        self.assertEqual(self.model.SeatParameters(axial_mm=-0.5).depth_mm, 6.5)

    def test_invalid_or_infeasible_geometry_is_rejected_before_fusion(self):
        for values in ({'outside_mm': 0}, {'width_mm': -1}, {'axial_mm': -7},
                       {'correction_mm': -22}, {'land_count': 4}, {'land_count': 5.0},
                       {'land_degrees': 80}, {'relief_mm': 0.5},
                       {'rotation_degrees': float('nan')}):
            with self.assertRaises(ValueError):
                self.model.SeatParameters(**values).validate()

    def test_midpoints_follow_the_correct_clockwise_or_counterclockwise_arcs(self):
        segments = self.model.SeatParameters().segments()
        for segment in segments:
            if segment.radius is None:
                continue
            middle = self.model.arc_midpoint(segment)
            self.assertAlmostEqual(math.dist(middle, segment.center), segment.radius)
            # All sector arcs are minor arcs; the midpoint lies between the intended endpoints.
            self.assertLess(math.dist(middle, segment.start), math.dist(segment.start, segment.end))
            self.assertLess(math.dist(middle, segment.end), math.dist(segment.start, segment.end))

    def test_optional_clearances_preserve_original_defaults(self):
        parameters = self.model.SeatParameters()
        parameters.validate()
        self.assertEqual(parameters.shaft_mode, 'Off')
        self.assertFalse(parameters.inner_relief_enabled)
        self.assertIsNone(parameters.snapshot_values()['shaft_diameter_mm'])

    def test_blind_shaft_and_inner_relief_use_independent_depth_references(self):
        parameters = self.model.SeatParameters(shaft_mode='Blind', axial_mm=0.5,
            blind_depth_mm=10, inner_relief_enabled=True, inner_diameter_mm=12, inner_depth_mm=0.4)
        parameters.validate()
        self.assertAlmostEqual(parameters.shaft_diameter_mm, 8.2)
        self.assertEqual(parameters.depth_mm, 7.5)
        self.assertAlmostEqual(parameters.inner_bottom_mm, 7.9)
        self.assertEqual(parameters.blind_depth_mm, 10)

    def test_invalid_clearances_cannot_remove_the_support_or_end_above_the_relief(self):
        invalid = ({'shaft_allowance_mm': 0}, {'bore_mm': 0}, {'shaft_allowance_mm': 20},
            {'blind_depth_mm': 7}, {'inner_relief_enabled': True, 'inner_diameter_mm': 0},
            {'inner_relief_enabled': True, 'inner_diameter_mm': 8.1},
            {'inner_relief_enabled': True, 'inner_diameter_mm': 21.9},
            {'inner_relief_enabled': True, 'inner_diameter_mm': 12, 'inner_depth_mm': 0},
            {'inner_relief_enabled': True, 'inner_diameter_mm': 12, 'blind_depth_mm': 7.3})
        for values in invalid:
            with self.assertRaises(ValueError):
                self.model.SeatParameters(**dict({'shaft_mode': 'Blind'}, **values)).validate()
        with self.assertRaises(ValueError):
            self.model.SeatParameters(inner_relief_enabled=True, inner_diameter_mm=12).validate()

    def test_through_all_ignores_inactive_blind_depth_but_keeps_manual_relief_validation(self):
        self.model.SeatParameters(shaft_mode='Through All', blind_depth_mm=0,
            inner_relief_enabled=True, inner_diameter_mm=12).validate()

    def test_missing_manual_inner_diameter_reports_current_value_and_effective_bounds(self):
        with self.assertRaises(ValueError) as raised:
            self.model.SeatParameters(shaft_mode='Through All', shaft_allowance_mm=0.5,
                                      inner_relief_enabled=True, inner_diameter_mm=0).validate()
        message = str(raised.exception)
        self.assertIn('8.500 mm', message)
        self.assertIn('21.900 mm', message)
        self.assertIn('Current value: 0.000 mm', message)

    def test_bore_preset_keeps_preview_valid_without_a_fabricated_relief(self):
        parameters = self.model.SeatParameters(shaft_mode='Through All', inner_relief_enabled=True)
        parameters.validate()
        self.assertEqual(parameters.inner_diameter_mm, parameters.bore_mm)
        self.assertTrue(parameters.inner_relief_pending)
        self.assertFalse(parameters.has_inner_relief)
        self.assertFalse(parameters.snapshot_values()['inner_relief_applied'])

    def test_pending_relief_does_not_require_a_deeper_blind_shaft_pocket(self):
        parameters = self.model.SeatParameters(shaft_mode='Blind', blind_depth_mm=7.2,
                                               inner_relief_enabled=True)
        parameters.validate()
        with self.assertRaises(ValueError):
            self.model.SeatParameters(shaft_mode='Blind', blind_depth_mm=7.2,
                inner_relief_enabled=True, inner_diameter_mm=12).validate()
