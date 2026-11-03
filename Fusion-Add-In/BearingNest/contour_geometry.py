"""Confirmed contour A in millimetres; no Fusion API dependencies."""
from dataclasses import dataclass
import math
from pathlib import Path


def polar(radius, angle):
    return (radius * math.cos(angle), radius * math.sin(angle))


def rotate(point, angle):
    x, y = point
    return (x * math.cos(angle) - y * math.sin(angle),
            x * math.sin(angle) + y * math.cos(angle))


@dataclass(frozen=True)
class Segment:
    start: tuple
    end: tuple
    center: tuple = None
    radius: float = None
    clockwise: bool = False


def contour(diameter=21.9, count=5, land_degrees=30, depth=1.2, fillet=0.4):
    values = (diameter, land_degrees, depth, fillet)
    if not all(math.isfinite(v) and v > 0 for v in values):
        raise ValueError('Dimensions must be finite and positive.')
    if type(count) is not int or count not in (3, 5, 7, 9):
        raise ValueError('Land count must be 3, 5, 7 or 9.')
    r, outer = diameter / 2, diameter / 2 + depth
    pitch, half = 2 * math.pi / count, math.radians(land_degrees) / 2
    if fillet >= outer / 2:
        raise ValueError('Transition radius is too large.')
    offset_in = math.asin(fillet / (r + fillet))
    offset_out = math.asin(fillet / (outer - fillet))
    alpha, beta = half + offset_in, half + offset_in + offset_out
    if 2 * beta >= pitch:
        raise ValueError('Lands and transitions leave no relief arc.')
    inner_wall = math.sqrt((r + fillet)**2 - fillet**2)
    outer_wall = math.sqrt((outer - fillet)**2 - fillet**2)
    if outer_wall <= inner_wall:
        raise ValueError('Relief depth leaves no radial wall between the fillets.')
    contact = polar(r, half)
    wall_in, wall_out = polar(inner_wall, alpha), polar(outer_wall, alpha)
    relief = polar(outer, beta)
    inner_center = polar(r + fillet, half)
    outer_center = polar(outer - fillet, beta)
    flank = [Segment(contact, wall_in, inner_center, fillet, True),
             Segment(wall_in, wall_out),
             Segment(wall_out, relief, outer_center, fillet)]

    def reflect(point):
        return rotate((point[0], -point[1]), pitch)

    sector = [Segment(polar(r, -half), contact, (0, 0), r), *flank,
              Segment(relief, reflect(relief), (0, 0), outer)]
    for segment in reversed(flank):
        sector.append(Segment(reflect(segment.end), reflect(segment.start),
                              reflect(segment.center) if segment.center else None,
                              segment.radius, segment.clockwise))
    result = []
    for index in range(count):
        angle = index * pitch
        for segment in sector:
            result.append(Segment(rotate(segment.start, angle), rotate(segment.end, angle),
                                  rotate(segment.center, angle) if segment.center else None,
                                  segment.radius, segment.clockwise))
    return result

