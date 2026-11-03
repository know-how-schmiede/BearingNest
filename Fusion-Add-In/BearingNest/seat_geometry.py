"""Atomic seat batches on one root-component face, within command transactions."""
import math
import adsk.core
import adsk.fusion
from . import seat_snapshot, seat_storage
from .seat_parameters import mm_to_cm, arc_midpoint


def placement(design, face, point_entity):
    if design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
        raise ValueError('The prototype requires a parametric design with design history enabled.')
    root = design.rootComponent
    if (face.assemblyContext is not None or face.body.parentComponent != root
            or not face.body.isSolid):
        raise ValueError('Select a planar face on a solid body in the root component.')
    plane = adsk.core.Plane.cast(face.geometry)
    if plane is None:
        raise ValueError('The selected face must be planar.')
    if getattr(point_entity, 'assemblyContext', None) is not None:
        raise ValueError('Assembly-context positions are not supported by this prototype.')
    if isinstance(point_entity, adsk.fusion.SketchPoint):
        if point_entity.parentSketch.parentComponent != root:
            raise ValueError('Select a position in the root component.')
        point = point_entity.worldGeometry
    elif isinstance(point_entity, adsk.fusion.BRepVertex):
        if point_entity.body.parentComponent != root:
            raise ValueError('Select a position in the root component.')
        point = point_entity.geometry
    elif isinstance(point_entity, adsk.fusion.BRepEdge):
        if point_entity.body.parentComponent != root:
            raise ValueError('Select a position in the root component.')
        circle = adsk.core.Circle3D.cast(point_entity.geometry)
        if circle is None:
            raise ValueError('Only circular edges can supply a center.')
        point = circle.center
    else:
        raise ValueError('Select a sketch point, vertex or circular edge center.')
    normal = plane.normal.copy()
    normal.normalize()
    if abs(plane.origin.vectorTo(point).dotProduct(normal)) > 1e-6:
        raise ValueError('The position must lie on the selected face plane.')
    if face.isParamReversed:
        normal.scaleBy(-1)
    return point, normal


def _fully_contained(manager, tool, target, inward):
    """Compare actual contour-tool volume, not an enclosing cylinder or sparse samples."""
    volume = tool.volume
    if volume <= 0:
        raise ValueError('The seat tool is not a solid.')
    for floor_probe in (False, True):
        intersection = manager.copy(tool)
        if intersection is None:
            raise RuntimeError('Could not copy the temporary containment tool.')
        if floor_probe:
            # Verify a positive floor remains below the complete contour (0.001 mm tolerance).
            translation = inward.copy()
            translation.scaleBy(mm_to_cm(0.001))
            transform = adsk.core.Matrix3D.create()
            transform.translation = translation
            if not manager.transform(intersection, transform):
                raise RuntimeError('Could not check the seat floor.')
        if not manager.booleanOperation(intersection, target,
                                        adsk.fusion.BooleanTypes.IntersectionBooleanType):
            raise ValueError('The proposed seat does not lie inside the selected body.')
        if abs(intersection.volume - volume) > max(1e-9, volume * 1e-7):
            raise ValueError('The proposed seat breaks out of the body or intersects an existing void.')


def _extrude(design, sketch, parameters, direction, operation, body=None):
    extrudes = design.rootComponent.features.extrudeFeatures
    feature_input = extrudes.createInput(sketch.profiles.item(0), operation)
    extent = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString(f'{parameters.depth_mm:.12g} mm'))
    if not feature_input.setOneSideExtent(extent, direction):
        raise RuntimeError('Could not define the seat depth.')
    if body is not None:
        feature_input.participantBodies = [body]
    feature = extrudes.add(feature_input)
    if feature is None:
        raise RuntimeError('Could not extrude the bearing seat.')
    return feature


def _prepare_seat(design, face, point, outward, parameters, created):
    """Build the contour and a hidden validation tool; no cut is made here."""
    sketch = design.rootComponent.sketches.addWithoutEdges(face)
    if sketch is None:
        raise RuntimeError('Could not create the seat sketch.')
    created.append(sketch)
    sketch.name = 'BearingNest - contour A'
    # Keep the same sketch/profile state as the working 0.1.2 construction path.
    # Suppress display only after the profile has been consumed by the final cut.
    sketch.areProfilesShown = True
    sketch.isVisible = True
    center = sketch.modelToSketchSpace(point)
    angle = math.radians(parameters.rotation_degrees)
    cos_a, sin_a = math.cos(angle), math.sin(angle)

    def sketch_point(xy):
        x, y = xy
        return adsk.core.Point3D.create(center.x + mm_to_cm(x * cos_a - y * sin_a),
                                       center.y + mm_to_cm(x * sin_a + y * cos_a), 0)

    sketch.isComputeDeferred = True
    try:
        for segment in parameters.segments():
            if segment.radius is None:
                curve = sketch.sketchCurves.sketchLines.addByTwoPoints(
                    sketch_point(segment.start), sketch_point(segment.end))
            else:
                curve = sketch.sketchCurves.sketchArcs.addByThreePoints(
                    sketch_point(segment.start), sketch_point(arc_midpoint(segment)),
                    sketch_point(segment.end))
            if curve is None:
                raise RuntimeError('Could not construct a contour segment.')
            curve.isFixed = True
    finally:
        sketch.isComputeDeferred = False
    profile_count = sketch.profiles.count
    if profile_count != 1:
        raise ValueError(f'The seat sketch must contain exactly one closed profile (found {profile_count}).')
    origin = sketch.sketchToModelSpace(adsk.core.Point3D.create(0, 0, 0))
    z_point = sketch.sketchToModelSpace(adsk.core.Point3D.create(0, 0, 1))
    normal = origin.vectorTo(z_point)
    normal.normalize()
    alignment = normal.dotProduct(outward)
    if abs(alignment) < 0.999:
        raise ValueError('The sketch normal could not be matched to the selected face.')
    direction = (adsk.fusion.ExtentDirections.NegativeExtentDirection if alignment > 0
                 else adsk.fusion.ExtentDirections.PositiveExtentDirection)
    feature = _extrude(design, sketch, parameters, direction,
                       adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    created.append(feature)
    feature.name = 'BearingNest - validation tool'
    if feature.bodies.count != 1:
        raise ValueError('The contour must create one solid tool body.')
    tool = feature.bodies.item(0)
    tool.isVisible = False
    inward = outward.copy()
    inward.scaleBy(-1)
    manager = adsk.fusion.TemporaryBRepManager.get()
    _fully_contained(manager, tool, face.body, inward)
    envelope = manager.copy(tool)
    if envelope is None:
        raise RuntimeError('Could not retain the temporary overlap-check envelope.')
    return dict(sketch=sketch, tool_feature=feature, envelope=envelope, direction=direction)


def _check_overlap(manager, first, second):
    """A difference retains the full volume only for disjoint solid envelopes."""
    first_box, second_box = first.boundingBox, second.boundingBox
    if any(getattr(first_box.maxPoint, axis) <= getattr(second_box.minPoint, axis)
           or getattr(second_box.maxPoint, axis) <= getattr(first_box.minPoint, axis)
           for axis in ('x', 'y', 'z')):
        return
    remaining = manager.copy(first)
    if remaining is None:
        raise RuntimeError('Could not create the overlap-check envelope.')
    volume = remaining.volume
    if not manager.booleanOperation(remaining, second,
                                    adsk.fusion.BooleanTypes.DifferenceBooleanType):
        raise ValueError('Seat envelopes overlap or their separation could not be verified.')
    if abs(remaining.volume - volume) > max(1e-9, volume * 1e-7):
        raise ValueError('Seat envelopes overlap.')


def _hide_position_fills(positions, changed):
    """Keep selected points/curves visible, but remove coplanar filled sketch overlays."""
    for position in positions:
        if isinstance(position, adsk.fusion.SketchPoint):
            sketch = position.parentSketch
            if all(sketch != item[0] for item in changed):
                changed.append((sketch, sketch.areProfilesShown))
                sketch.areProfilesShown = False


def create_seats(design, face, positions, parameters, *, persist):
    """Validate every position and pair before the first cut, in one command transaction."""
    parameters.validate()
    positions = list(positions)
    if not positions:
        raise ValueError('Select at least one seat position.')
    # Resolve all placements and references before model topology can change.
    placements = []
    for index, position in enumerate(positions, 1):
        try:
            point, outward = placement(design, face, position)
        except Exception as error:
            raise ValueError(f'Position {index}: {error}') from error
        for previous_index, (previous, _, _) in enumerate(placements, 1):
            if point.distanceTo(previous) < 1e-6:
                raise ValueError(f'Positions {previous_index} and {index} have the same center.')
        references = {'face': face.entityToken, 'position': position.entityToken,
                      'body': face.body.entityToken}
        placements.append((point, outward, references))

    created, prepared, cuts, shading = [], [], [], []
    manager = adsk.fusion.TemporaryBRepManager.get()
    try:
        for index, (point, outward, references) in enumerate(placements, 1):
            try:
                item = _prepare_seat(design, face, point, outward, parameters, created)
                for previous_index, previous in enumerate(prepared, 1):
                    try:
                        _check_overlap(manager, previous['envelope'], item['envelope'])
                    except Exception as error:
                        raise ValueError(f'Positions {previous_index} and {index}: {error}') from error
                item['references'] = references
                prepared.append(item)
            except Exception as error:
                raise ValueError(f'Position {index}: {error}') from error

        # Delete validation extrusions BEFORE direct cuts, avoiding retained coplanar tool faces.
        for item in reversed(prepared):
            if not item['tool_feature'].deleteMe():
                raise RuntimeError('Could not remove a validation tool; no seats were committed.')
        if persist:
            _hide_position_fills(positions, shading)
        body = face.body
        for index, item in enumerate(prepared, 1):
            cut = _extrude(design, item['sketch'], parameters, item['direction'],
                           adsk.fusion.FeatureOperations.CutFeatureOperation, body)
            created.append(cut)
            cut.name = f'BearingNest - bearing seat {index}'
            if cut.bodies.count != 1:
                raise ValueError('The cut must leave one resulting body.')
            body = cut.bodies.item(0)
            item['sketch'].isVisible = False
            item['sketch'].areProfilesShown = True
            cuts.append(cut)

        if persist:
            for cut, item in zip(cuts, prepared):
                snapshot = seat_snapshot.create(parameters=parameters.snapshot_values(),
                    bearing={'D_mm': parameters.outside_mm, 'B_mm': parameters.width_mm,
                             'd_mm': None, 'inner_ring_outside_mm': None, 'source': 'manual'},
                    profile={'name': 'Manual prototype values'}, auto_flags={},
                    references=item['references'],
                    features={'contour': item['sketch'].entityToken, 'seat_cut': cut.entityToken})
                seat_storage.save(cut, snapshot)
        return cuts
    except Exception:
        failures = []
        for entity in reversed(created):
            try:
                if entity.isValid and not entity.deleteMe():
                    failures.append('feature cleanup')
            except Exception:
                failures.append('feature cleanup')
        for sketch, original in reversed(shading):
            try:
                if sketch.isValid:
                    sketch.areProfilesShown = original
            except Exception:
                failures.append('profile display restore')
        if failures:
            raise RuntimeError('Seat cleanup failed; cancel the command to roll back the transaction.')
        raise


def create_seat(design, face, position, parameters, *, persist):
    """Compatibility wrapper for callers creating exactly one seat."""
    return create_seats(design, face, [position], parameters, persist=persist)[0]
