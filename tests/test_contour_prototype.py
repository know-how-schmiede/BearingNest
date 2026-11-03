"""Geometric invariants for the review contour; no Fusion API involved."""
import math
from pathlib import Path
import runpy
import unittest

MODEL = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'tools/contour_prototype.py'))


class ContourTests(unittest.TestCase):
    def test_closed_tangent_contours_for_all_land_counts(self):
        for count in (3, 5, 7, 9):
            segments = MODEL['contour'](count=count, land_degrees=20)
            for index, first in enumerate(segments):
                second = segments[(index + 1) % len(segments)]
                self.assertLess(math.dist(first.end, second.start), 1e-10)
                tangents = []
                for segment, point in ((first, first.end), (second, second.start)):
                    if segment.radius:
                        vector = (point[0] - segment.center[0], point[1] - segment.center[1])
                        self.assertAlmostEqual(math.hypot(*vector), segment.radius)
                        sign = -1 if segment.clockwise else 1
                        vector = (-sign * vector[1], sign * vector[0])
                    else:
                        vector = (segment.end[0] - segment.start[0], segment.end[1] - segment.start[1])
                    length = math.hypot(*vector)
                    tangents.append((vector[0] / length, vector[1] / length))
                self.assertLess(math.dist(*tangents), 1e-10)

    def test_infeasible_dimensions_are_rejected(self):
        for parameters in ({'depth': 0.5}, {'land_degrees': 72}, {'count': 4},
                           {'fillet': float('nan')}, {'diameter': 0}):
            with self.assertRaises(ValueError):
                MODEL['contour'](**parameters)


if __name__ == '__main__':
    unittest.main()
