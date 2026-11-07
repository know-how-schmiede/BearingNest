"""Replay a validated new-seat preview as owned transient BRep graphics."""
import adsk.fusion


class CachedPreview:
    def __init__(self, body, feedback):
        self.body = adsk.fusion.TemporaryBRepManager.get().copy(body)
        if self.body is None:
            raise RuntimeError('Could not copy the validated preview body.')
        # Points/vectors are detached placement values; do not deepcopy API wrappers.
        self.feedback = dict(placements=dict(feedback['placements']),
            issues={key: list(value) for key, value in feedback['issues'].items()},
            warnings={key: list(value) for key, value in feedback['warnings'].items()})
        self.group = None
        self.source = None
        self.source_opacity = None

    def clear(self):
        # Restore appearance even if graphics cleanup fails. Keep failed ownership
        # for a later cleanup retry rather than silently abandoning it.
        try:
            if self.group is not None:
                if self.group.isValid and not self.group.deleteMe():
                    raise RuntimeError('Could not remove cached BearingNest preview graphics.')
                self.group = None
        finally:
            if self.source is not None:
                if not self.source.isValid:
                    raise RuntimeError('Could not restore the cached preview source body.')
                self.source.opacity = self.source_opacity
                self.source = None

    def show(self, design, source):
        self.clear()
        # Keep originally invisible bodies invisible; use the normal preview path.
        if not source.isVisible:
            raise RuntimeError('Cached preview requires a visible source body.')
        self.group = design.rootComponent.customGraphicsGroups.add()
        if self.group is None:
            raise RuntimeError('Could not create cached preview graphics.')
        try:
            graphics = self.group.addBRepBody(self.body)
            if graphics is None:
                raise RuntimeError('Could not display cached preview graphics.')
            graphics.isSelectable = False
            graphics.color = adsk.fusion.CustomGraphicsAppearanceColorEffect.create(source.appearance)
            graphics.setOpacity(source.visibleOpacity, True)
            # Keep the native body available to face/vertex/edge selection. Its
            # display is replaced by the validated cut result, not a hidden body.
            self.source, self.source_opacity = source, source.opacity
            source.opacity = 0.0
        except Exception:
            self.clear()
            raise
