"""Batch diagnostics and approximate marker math, independent of Fusion."""
import math


class BatchValidationError(ValueError):
    def __init__(self, messages):
        super().__init__('\n'.join(messages))


def new_feedback():
    return dict(placements={}, issues={}, warnings={})


def add_message(feedback, section, indices, message):
    for index in indices:
        messages = feedback[section].setdefault(index, [])
        if message not in messages:
            messages.append(message)


def marker_lines(center, normal, radius_cm, samples=64):
    """Circle and cross on any plane; packed independent line pairs in world cm."""
    length = math.sqrt(sum(value * value for value in normal))
    if (length <= 0 or not math.isfinite(length) or not math.isfinite(radius_cm) or radius_cm <= 0
            or not all(math.isfinite(value) for value in center)
            or type(samples) is not int or samples < 8):
        raise ValueError('A marker requires a finite normal and positive radius.')
    n = tuple(value / length for value in normal)
    helper = (1, 0, 0) if abs(n[0]) < 0.9 else (0, 1, 0)
    u = (n[1]*helper[2]-n[2]*helper[1], n[2]*helper[0]-n[0]*helper[2], n[0]*helper[1]-n[1]*helper[0])
    size = math.sqrt(sum(v*v for v in u))
    u = tuple(v/size for v in u)
    v = (n[1]*u[2]-n[2]*u[1], n[2]*u[0]-n[0]*u[2], n[0]*u[1]-n[1]*u[0])

    def point(x, y):
        return [center[k] + radius_cm * (u[k]*x + v[k]*y) for k in range(3)]

    coordinates = []
    for index in range(samples):
        a, b = math.tau*index/samples, math.tau*(index+1)/samples
        coordinates.extend(point(math.cos(a), math.sin(a)))
        coordinates.extend(point(math.cos(b), math.sin(b)))
    for a, b in (((-0.7, -0.7), (0.7, 0.7)), ((-0.7, 0.7), (0.7, -0.7))):
        coordinates.extend(point(*a))
        coordinates.extend(point(*b))
    return coordinates
