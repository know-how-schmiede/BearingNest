"""Owned, transient graphics for invalid seats and advisory wall warnings."""
import adsk.core
import adsk.fusion
from .seat_feedback import marker_lines
from .strings import TEXT


class PreviewGraphics:
    def __init__(self):
        self.group = None

    def clear(self):
        if self.group is not None:
            if self.group.isValid and not self.group.deleteMe():
                raise RuntimeError(TEXT['marker_cleanup_failed'])
            self.group = None

    def show(self, design, feedback, radius_mm):
        self.clear()
        indices = sorted(set(feedback['issues']) | set(feedback['warnings']))
        if feedback['issues']:
            indices = sorted(feedback['placements'])
        drawable = [i for i in indices if i in feedback['placements']]
        if not drawable:
            return
        self.group = design.rootComponent.customGraphicsGroups.add()
        if self.group is None:
            raise RuntimeError(TEXT['marker_creation_failed'])
        try:
            for index in drawable:
                point, normal = feedback['placements'][index]
                packed = marker_lines((point.x, point.y, point.z), (normal.x, normal.y, normal.z), radius_mm / 10)
                coordinates = adsk.fusion.CustomGraphicsCoordinates.create(packed)
                lines = self.group.addLines(coordinates, [], False)
                if lines is None:
                    raise RuntimeError(TEXT['marker_creation_failed'])
                rgb = ((230, 35, 35) if index in feedback['issues'] else
                       (230, 145, 0) if index in feedback['warnings'] else (35, 130, 230))
                color = adsk.core.Color.create(*rgb, 255)
                lines.color = adsk.fusion.CustomGraphicsSolidColorEffect.create(color)
                lines.showThrough = adsk.fusion.CustomGraphicsShowThroughColorEffect.create(color, 0.8)
                lines.weight = 3
                lines.isSelectable = False
        except Exception:
            self.clear()
            raise
