"""Atomic seat batches on one root-component face, within command transactions."""
import math
from uuid import uuid4
import adsk.core
import adsk.fusion
from . import seat_snapshot, seat_storage
from .seat_parameters import mm_to_cm, arc_midpoint
from .seat_feedback import BatchValidationError, new_feedback, add_message
from .strings import TEXT


def verify_rebuild(design, entities):
    """Recompute after deleting originals; reject cascaded feature loss/errors."""
    if not design.computeAll():
        raise RuntimeError('Fusion could not recompute the replaced seat sequence.')
    for entity in entities:
        if (not entity.isValid
                or entity.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState):
            raise RuntimeError('A replacement feature was lost or became unhealthy; the command must roll back.')


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


def _marker_location(face, position):
    """Best-effort world location for a rejected placement; never a validation bypass."""
    try:
        plane = adsk.core.Plane.cast(face.geometry)
        if plane is None or getattr(position, 'assemblyContext', None) is not None:
            return None
        if isinstance(position, adsk.fusion.SketchPoint):
            point = position.worldGeometry
        elif isinstance(position, adsk.fusion.BRepVertex):
            point = position.geometry
        elif isinstance(position, adsk.fusion.BRepEdge):
            circle = adsk.core.Circle3D.cast(position.geometry)
            point = circle.center if circle is not None else None
        else:
            return None
        return (point, plane.normal.copy()) if point is not None else None
    except Exception:
        return None


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


def _extrude(design, sketch, parameters, direction, operation, body=None, *,
             depth_mm=None, start_mm=0.0, through_all=False):
    extrudes = design.rootComponent.features.extrudeFeatures
    feature_input = extrudes.createInput(sketch.profiles.item(0), operation)
    if start_mm:
        sign = -1 if direction == adsk.fusion.ExtentDirections.NegativeExtentDirection else 1
        feature_input.startExtent = adsk.fusion.OffsetStartDefinition.create(
            adsk.core.ValueInput.createByString(f'{sign * start_mm:.12g} mm'))
    if through_all:
        extent = adsk.fusion.ThroughAllExtentDefinition.create()
        # A single-sided ThroughAllExtentDefinition has its own direction flag.
        extent.isPositiveDirection = direction == adsk.fusion.ExtentDirections.PositiveExtentDirection
    else:
        distance = parameters.depth_mm if depth_mm is None else depth_mm
        extent = adsk.fusion.DistanceExtentDefinition.create(
            adsk.core.ValueInput.createByString(f'{distance:.12g} mm'))
    if not feature_input.setOneSideExtent(extent, direction):
        raise RuntimeError('Could not define the seat depth.')
    if body is not None:
        feature_input.participantBodies = [body]
    before_volume = body.volume if body is not None else None
    feature = extrudes.add(feature_input)
    if feature is None:
        raise RuntimeError('Could not extrude the bearing seat.')
    try:
        if feature.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
            detail = feature.errorOrWarningMessage or 'The extrusion is not healthy.'
            raise RuntimeError(f'Fusion extrusion failed: {detail}')
        if body is not None:
            if feature.bodies.count != 1:
                raise ValueError('The cut must leave one resulting body.')
            after_volume = feature.bodies.item(0).volume
            if not all(math.isfinite(value) for value in (before_volume, after_volume)):
                raise ValueError('The cut volume could not be verified.')
            if before_volume - after_volume <= max(1e-9, before_volume * 1e-10):
                raise ValueError('The cut removed no material. Check its direction, start plane and target body.')
    except Exception:
        # Callers cannot yet own a feature that failed inside this helper.
        if feature.isValid and not feature.deleteMe():
            raise RuntimeError('Could not clean up the failed extrusion; cancel the command.')
        raise
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
    direction = _inward_direction(sketch, outward)
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


def _inward_direction(sketch, outward):
    origin = sketch.sketchToModelSpace(adsk.core.Point3D.create(0, 0, 0))
    z_point = sketch.sketchToModelSpace(adsk.core.Point3D.create(0, 0, 1))
    normal = origin.vectorTo(z_point)
    normal.normalize()
    alignment = normal.dotProduct(outward)
    if abs(alignment) < 0.999:
        raise ValueError('The sketch normal could not be matched to the selected face.')
    return (adsk.fusion.ExtentDirections.NegativeExtentDirection if alignment > 0
            else adsk.fusion.ExtentDirections.PositiveExtentDirection)


def _through_depth_mm(body, point, inward):
    """Finite preflight tool covering the body; the final cut uses native Through All."""
    box = body.boundingBox
    maximum = max(point.vectorTo(adsk.core.Point3D.create(x, y, z)).dotProduct(inward)
                  for x in (box.minPoint.x, box.maxPoint.x)
                  for y in (box.minPoint.y, box.maxPoint.y)
                  for z in (box.minPoint.z, box.maxPoint.z))
    if maximum <= 0:
        raise ValueError('No body material lies along the shaft direction.')
    return maximum * 10.0 + 1.0


def _prepare_round_cut(design, face, point, outward, parameters, created, *,
                       kind, diameter_mm, depth_mm, start_mm, through_all):
    sketch = design.rootComponent.sketches.addWithoutEdges(face)
    if sketch is None:
        raise RuntimeError('Could not create the circular clearance sketch.')
    created.append(sketch)
    sketch.name = f'BearingNest - {kind}'
    sketch.areProfilesShown = True
    sketch.isVisible = True
    center = sketch.modelToSketchSpace(point)
    center.z = 0
    circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(center, mm_to_cm(diameter_mm / 2))
    if circle is None:
        raise RuntimeError('Could not create the clearance circle.')
    circle.isFixed = True
    if sketch.profiles.count != 1:
        raise ValueError('The clearance sketch must contain one circular profile.')
    direction = _inward_direction(sketch, outward)
    inward = outward.copy()
    inward.scaleBy(-1)
    validation_depth = (_through_depth_mm(face.body, point, inward) if through_all else depth_mm)
    feature = _extrude(design, sketch, parameters, direction,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        depth_mm=validation_depth, start_mm=start_mm)
    created.append(feature)
    feature.name = f'BearingNest - {kind} validation tool'
    if feature.bodies.count != 1:
        raise ValueError('A clearance must create one solid validation tool.')
    tool = feature.bodies.item(0)
    tool.isVisible = False
    manager = adsk.fusion.TemporaryBRepManager.get()
    if not through_all:
        _fully_contained(manager, tool, face.body, inward)
    # Through All intentionally exits the target; its extrusion is scoped to that body.
    envelope = manager.copy(tool)
    if envelope is None:
        raise RuntimeError('Could not retain a clearance validation envelope.')
    return dict(kind=kind, sketch=sketch, tool_feature=feature, envelope=envelope,
                depth_mm=depth_mm, start_mm=start_mm, through_all=through_all, direction=direction)


def _prepare_extras(design, face, point, outward, parameters, created):
    extras = []
    if parameters.chamfer_mm:
        extras.append(_prepare_round_cut(design, face, point, outward, parameters, created,
            kind='chamfer_envelope',
            diameter_mm=parameters.contact_mm + 2 * (parameters.relief_mm + parameters.chamfer_mm),
            depth_mm=parameters.chamfer_mm, start_mm=0, through_all=False))
    if parameters.shaft_mode != 'Off':
        extras.append(_prepare_round_cut(design, face, point, outward, parameters, created,
            kind='shaft_cut', diameter_mm=parameters.shaft_diameter_mm,
            depth_mm=parameters.blind_depth_mm, start_mm=0,
            through_all=parameters.shaft_mode == 'Through All'))
    if parameters.has_inner_relief:
        extras.append(_prepare_round_cut(design, face, point, outward, parameters, created,
            kind='inner_ring_relief', diameter_mm=parameters.inner_diameter_mm,
            depth_mm=parameters.inner_depth_mm, start_mm=parameters.depth_mm,
            through_all=False))
    return extras


def _chamfer(design, cut, point, outward, distance_mm, created):
    """Chamfer only the seat rim on the original placement plane, not its floor."""
    edges = adsk.core.ObjectCollection.create()
    selected = []
    for side in cut.sideFaces:
        for edge in side.edges:
            if any(edge == previous for previous in selected):
                continue
            ok, low, high = edge.evaluator.getParameterExtents()
            if not ok:
                raise ValueError('Could not inspect the seat rim.')
            ok, samples = edge.evaluator.getPointsAtParameters([low, (low + high) / 2, high])
            if not ok:
                raise ValueError('Could not inspect the seat rim.')
            if all(abs(point.vectorTo(sample).dotProduct(outward)) < 1e-6 for sample in samples):
                edges.add(edge)
                selected.append(edge)
    if not selected:
        raise ValueError('No complete seat rim was found for the lead-in chamfer.')
    chamfers = design.rootComponent.features.chamferFeatures
    request = chamfers.createInput2()
    request.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        edges, adsk.core.ValueInput.createByString(f'{distance_mm:.12g} mm'), False)
    before = cut.bodies.item(0).volume
    feature = chamfers.add(request)
    if feature is None:
        raise ValueError('Fusion could not create the lead-in chamfer.')
    created.append(feature)
    feature.name = 'BearingNest - lead-in chamfer'
    if (feature.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
            or feature.bodies.count != 1):
        raise ValueError('The lead-in chamfer is not healthy; reduce its size.')
    after = feature.bodies.item(0).volume
    if not math.isfinite(after) or before - after <= max(1e-9, before * 1e-10):
        raise ValueError('The lead-in chamfer removed no measurable material.')
    return feature


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


def _wall_warnings(manager, body, placements, prepared, parameters, threshold_mm, feedback):
    """Conservative enclosing-cylinder margin probes; advisory, never a cut gate.

    Probes start at their intended opening plane and extend inward only. A native
    Through All shaft's exit is deliberately excluded from the floor check.
    """
    for index, (point, outward, _) in enumerate(placements, 1):
        operations = [(parameters.contact_mm / 2 + parameters.relief_mm, parameters.depth_mm, 0)]
        if parameters.chamfer_mm:
            operations.append((parameters.contact_mm / 2 + parameters.relief_mm + parameters.chamfer_mm,
                               parameters.chamfer_mm, 0))
        if parameters.shaft_mode == 'Blind':
            operations.append((parameters.shaft_diameter_mm / 2, parameters.blind_depth_mm, 0))
        if parameters.has_inner_relief:
            operations.append((parameters.inner_diameter_mm / 2, parameters.inner_depth_mm, parameters.depth_mm))
        inward = outward.copy()
        inward.scaleBy(-1)
        for radius, depth, start in operations:
            try:
                def at(distance_mm):
                    offset = mm_to_cm(distance_mm)
                    return adsk.core.Point3D.create(point.x + inward.x * offset,
                        point.y + inward.y * offset, point.z + inward.z * offset)
                expanded = mm_to_cm(radius + threshold_mm)
                probe = manager.createCylinderOrCone(at(start), expanded, at(start + depth + threshold_mm), expanded)
                if probe is None:
                    raise RuntimeError('Could not create the wall margin probe.')
                try:
                    _fully_contained(manager, probe, body, inward)
                except ValueError:
                    add_message(feedback, 'warnings', [index], TEXT['wall_body_warning'].format(
                        index=index, threshold=threshold_mm))
                for other in prepared:
                    if other['index'] == index:
                        continue
                    try:
                        for cut in [other, *other['extras']]:
                            _check_overlap(manager, probe, cut['envelope'])
                    except ValueError:
                        first, second = sorted((index, other['index']))
                        add_message(feedback, 'warnings', [first, second], TEXT['wall_pair_warning'].format(
                            first=first, second=second, threshold=threshold_mm))
            except Exception:
                # Advisory failure is visible, but cannot reject valid cut geometry.
                add_message(feedback, 'warnings', [index], TEXT['wall_check_unavailable'].format(index=index))


def create_seats(design, face, positions, parameters, *, persist, previous_snapshots=None, auto_flags=None,
                 bearing=None, profile=None, feedback=None, wall_threshold_mm=0,
                 generated_entities=None, preserve_metadata=False):
    """Validate every position and pair before the first cut, in one command transaction."""
    parameters.validate()
    if not math.isfinite(wall_threshold_mm) or wall_threshold_mm < 0:
        raise ValueError('Wall warning threshold must be finite and nonnegative.')
    if feedback is None:
        feedback = new_feedback()
    else:
        feedback.clear()
        feedback.update(new_feedback())
    positions = list(positions)
    if not positions:
        raise ValueError('Select at least one seat position.')
    if previous_snapshots is not None and len(previous_snapshots) != len(positions):
        raise ValueError('The edited batch must retain all its positions.')
    batch_id = (previous_snapshots[0].get('batch_id', str(uuid4()))
                if previous_snapshots else str(uuid4()))
    # Resolve all placements and references before model topology can change.
    placements = []
    errors = []
    for index, position in enumerate(positions, 1):
        try:
            point, outward = placement(design, face, position)
        except Exception as error:
            message = f'Position {index}: {error}'
            errors.append(message)
            add_message(feedback, 'issues', [index], message)
            location = _marker_location(face, position)
            if location is not None:
                feedback['placements'][index] = location
            placements.append(None)
            continue
        feedback['placements'][index] = (point, outward)
        for previous_index, previous in enumerate(placements, 1):
            if previous is not None and point.distanceTo(previous[0]) < 1e-6:
                message = f'Positions {previous_index} and {index} have the same center.'
                errors.append(message)
                add_message(feedback, 'issues', [previous_index, index], message)
        references = {'face': face.entityToken, 'position': position.entityToken,
                      'body': face.body.entityToken}
        placements.append((point, outward, references))
    if errors:
        raise BatchValidationError(errors)

    created, prepared, cuts, shading = [], [], [], []
    manager = adsk.fusion.TemporaryBRepManager.get()
    try:
        for index, (point, outward, references) in enumerate(placements, 1):
            try:
                item = _prepare_seat(design, face, point, outward, parameters, created)
                item['extras'] = _prepare_extras(design, face, point, outward, parameters, created)
                for previous in prepared:
                    previous_index = previous['index']
                    try:
                        for first in [previous, *previous['extras']]:
                            for second in [item, *item['extras']]:
                                _check_overlap(manager, first['envelope'], second['envelope'])
                    except Exception as error:
                        message = f'Positions {previous_index} and {index}: {error}'
                        errors.append(message)
                        add_message(feedback, 'issues', [previous_index, index], message)
                item['references'] = references
                item['index'] = index
                prepared.append(item)
            except ValueError as error:
                message = f'Position {index}: {error}'
                errors.append(message)
                add_message(feedback, 'issues', [index], message)
        if errors:
            raise BatchValidationError(errors)
        if wall_threshold_mm:
            try:
                _wall_warnings(manager, face.body, placements, prepared, parameters, wall_threshold_mm, feedback)
            except Exception:
                for index in range(1, len(placements) + 1):
                    add_message(feedback, 'warnings', [index], TEXT['wall_check_unavailable'].format(index=index))

        # Delete validation extrusions BEFORE direct cuts, avoiding retained coplanar tool faces.
        for item in reversed(prepared):
            for operation in reversed([item, *item['extras']]):
                if not operation['tool_feature'].deleteMe():
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
            item['features'] = {'contour': item['sketch'].entityToken, 'seat_cut': cut.entityToken}
            if parameters.chamfer_mm:
                point, outward, _ = placements[index - 1]
                chamfer = _chamfer(design, cut, point, outward, parameters.chamfer_mm, created)
                body = chamfer.bodies.item(0)
                item['features']['chamfer'] = chamfer.entityToken
            for operation in item['extras']:
                if operation['kind'] == 'chamfer_envelope':
                    if not operation['sketch'].deleteMe():
                        raise RuntimeError('Could not remove the chamfer validation sketch.')
                    continue
                clearance = _extrude(design, operation['sketch'], parameters, operation['direction'],
                    adsk.fusion.FeatureOperations.CutFeatureOperation, body,
                    depth_mm=operation['depth_mm'], start_mm=operation['start_mm'],
                    through_all=operation['through_all'])
                created.append(clearance)
                clearance.name = f"BearingNest - {operation['kind']} {index}"
                if clearance.bodies.count != 1:
                    raise ValueError('A clearance cut must leave one resulting body.')
                body = clearance.bodies.item(0)
                operation['sketch'].isVisible = False
                item['features'][operation['kind']] = clearance.entityToken
                item['features'][operation['kind'] + '_sketch'] = operation['sketch'].entityToken
            cuts.append(cut)

        if persist:
            for index, (cut, item) in enumerate(zip(cuts, prepared)):
                snapshot = seat_snapshot.create(parameters=parameters.snapshot_values(),
                    bearing=bearing if bearing is not None else {'D_mm': parameters.outside_mm, 'B_mm': parameters.width_mm,
                             'd_mm': parameters.bore_mm if parameters.shaft_mode != 'Off' else None,
                             'inner_ring_outside_mm': None, 'source': 'manual'},
                    profile=profile if profile is not None else {'name': 'Manual prototype values'}, auto_flags=auto_flags or {},
                    references=item['references'],
                    features=item['features'])
                snapshot['batch_id'] = batch_id
                if previous_snapshots:
                    old = previous_snapshots[index]
                    saved_bearing = old['bearing'] if preserve_metadata else bearing
                    if saved_bearing is None:
                        saved_bearing = dict(old['bearing'], D_mm=parameters.outside_mm,
                            B_mm=parameters.width_mm,
                            d_mm=parameters.bore_mm if parameters.shaft_mode != 'Off' else None)
                    snapshot = seat_snapshot.revise(old, parameters=snapshot['parameters'],
                        bearing=saved_bearing,
                        profile=old['profile'] if profile is None else profile,
                        auto_flags=old['auto_flags'] if auto_flags is None else dict(old['auto_flags'], **auto_flags),
                        references=snapshot['references'], features=snapshot['features'])
                    snapshot['batch_id'] = batch_id
                seat_storage.save(cut, snapshot)
        if generated_entities is not None:
            generated_entities.extend(entity for entity in created if entity.isValid)
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
