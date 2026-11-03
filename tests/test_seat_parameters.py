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
