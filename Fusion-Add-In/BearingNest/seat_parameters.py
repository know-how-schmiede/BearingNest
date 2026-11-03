"""Single-seat prototype parameters in mm/degrees, separate from the Fusion API."""
from dataclasses import dataclass, asdict
import math
from .contour_geometry import contour


@dataclass(frozen=True)
class SeatParameters:
    outside_mm: float = 22.0
    width_mm: float = 7.0
    correction_mm: float = -0.1
    axial_mm: float = 0.0
    land_count: int = 5
    land_degrees: float = 30.0
    rotation_degrees: float = 0.0
    relief_mm: float = 1.2
    fillet_mm: float = 0.4

    @property
    def contact_mm(self):
        return self.outside_mm + self.correction_mm

    @property
    def depth_mm(self):
        return self.width_mm + self.axial_mm

    def segments(self):
        self.validate()
        return contour(self.contact_mm, self.land_count, self.land_degrees,
                       self.relief_mm, self.fillet_mm)

    def validate(self):
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
                   for v in asdict(self).values()):
            raise ValueError('Seat dimensions must be finite numbers.')
        if self.outside_mm <= 0 or self.width_mm <= 0 or self.contact_mm <= 0 or self.depth_mm <= 0:
            raise ValueError('Bearing dimensions, contact diameter and seat depth must be positive.')
        if type(self.land_count) is not int:
            raise ValueError('Land count must be an integer.')
        contour(self.contact_mm, self.land_count, self.land_degrees, self.relief_mm, self.fillet_mm)

    def snapshot_values(self):
        self.validate()
        return dict(asdict(self), contact_mm=self.contact_mm, depth_mm=self.depth_mm)


def mm_to_cm(value):
    return value / 10.0


def arc_midpoint(segment):
    """A point on the intended signed arc, including clockwise fillet arcs."""
    x, y = segment.center
    start = math.atan2(segment.start[1] - y, segment.start[0] - x)
    end = math.atan2(segment.end[1] - y, segment.end[0] - x)
    sweep = (end - start) % (2 * math.pi)
    if segment.clockwise:
        sweep -= 2 * math.pi
    angle = start + sweep / 2
    return (x + segment.radius * math.cos(angle), y + segment.radius * math.sin(angle))
