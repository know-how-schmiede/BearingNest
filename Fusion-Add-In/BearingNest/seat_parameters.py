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
    shaft_mode: str = 'Off'
    bore_mm: float = 8.0
    shaft_allowance_mm: float = 0.2
    blind_depth_mm: float = 12.0
    inner_relief_enabled: bool = False
    inner_diameter_mm: float = 8.0
    inner_depth_mm: float = 0.4

    @property
    def shaft_diameter_mm(self):
        return self.bore_mm + self.shaft_allowance_mm

    @property
    def inner_bottom_mm(self):
        return self.depth_mm + self.inner_depth_mm

    @property
    def inner_relief_pending(self):
        return self.inner_relief_enabled and math.isclose(
            self.inner_diameter_mm, self.bore_mm, rel_tol=0, abs_tol=1e-9)

    @property
    def has_inner_relief(self):
        return self.inner_relief_enabled and not self.inner_relief_pending

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
                   for key, v in asdict(self).items()
                   if key not in ('shaft_mode', 'inner_relief_enabled')):
            raise ValueError('Seat dimensions must be finite numbers.')
        if self.outside_mm <= 0 or self.width_mm <= 0 or self.contact_mm <= 0 or self.depth_mm <= 0:
            raise ValueError('Bearing dimensions, contact diameter and seat depth must be positive.')
        if type(self.land_count) is not int:
            raise ValueError('Land count must be an integer.')
        if self.shaft_mode not in ('Off', 'Through All', 'Blind'):
            raise ValueError('Unknown shaft opening mode.')
        if type(self.inner_relief_enabled) is not bool:
            raise ValueError('Inner-ring relief mode must be Boolean.')
        if self.shaft_mode != 'Off':
            if self.bore_mm <= 0 or self.bore_mm >= self.outside_mm or self.shaft_allowance_mm <= 0:
                raise ValueError('Enter a positive bearing bore below the outside diameter and a positive shaft allowance.')
            if self.shaft_diameter_mm >= self.contact_mm:
                raise ValueError('The shaft opening must be smaller than the contact diameter.')
            required_bottom = self.inner_bottom_mm if self.has_inner_relief else self.depth_mm
            if self.shaft_mode == 'Blind' and self.blind_depth_mm <= required_bottom:
                raise ValueError('Blind shaft depth is measured from the selected face and must extend beyond the seat and inner-ring relief.')
        if self.inner_relief_enabled:
            if self.shaft_mode == 'Off':
                raise ValueError('Enable a shaft opening before adding inner-ring relief.')
            if not self.inner_relief_pending and not self.shaft_diameter_mm < self.inner_diameter_mm < self.contact_mm:
                raise ValueError(f'Enter Inner-ring relief diameter (manual) from the bearing drawing: '
                    f'greater than {self.shaft_diameter_mm:.3f} mm and less than {self.contact_mm:.3f} mm. '
                    f'Current value: {self.inner_diameter_mm:.3f} mm. Verify outer-ring support.')
            if self.inner_depth_mm <= 0:
                raise ValueError('Inner-ring relief depth from the seat floor must be positive.')
        contour(self.contact_mm, self.land_count, self.land_degrees, self.relief_mm, self.fillet_mm)

    def snapshot_values(self):
        self.validate()
        return dict(asdict(self), contact_mm=self.contact_mm, depth_mm=self.depth_mm,
                    shaft_diameter_mm=self.shaft_diameter_mm if self.shaft_mode != 'Off' else None,
                    inner_relief_pending=self.inner_relief_pending, inner_relief_applied=self.has_inner_relief)


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
