"""Constrained whole-batch editing inside Fusion command/preview transactions."""
from dataclasses import fields
from . import seat_snapshot, seat_storage, seat_geometry
from .seat_parameters import SeatParameters

FEATURE_ROLES = {'contour', 'seat_cut', 'chamfer', 'shaft_cut', 'shaft_cut_sketch',
                 'inner_ring_relief', 'inner_ring_relief_sketch'}


def batches(design):
    groups, errors = {}, []
    for attribute in seat_storage.discover(design):
        try:
            record = seat_snapshot.loads(attribute.value)
            identity = record.get('batch_id', record['seat_id'])
            if not isinstance(identity, str) or not identity:
                raise ValueError('Invalid batch identity.')
            groups.setdefault(identity, []).append(record)
        except Exception as error:
            errors.append(str(error))
    return list(groups.values()), errors


def parameters(record):
    values = record['parameters']
    result = SeatParameters(**{field.name: values[field.name]
                              for field in fields(SeatParameters) if field.name in values})
    result.validate()
    return result


def _unique(design, token, role):
    matches = design.findEntityByToken(token)
    if len(matches) != 1:
        raise ValueError(f'Repair required: {role} is missing or ambiguous.')
    return matches[0]


def editable_entities(design, records):
    """Reject downstream features, timeline groups and incomplete ownership before writes."""
    if not records or len({record['seat_id'] for record in records}) != len(records):
        raise ValueError('Invalid or duplicate seat records.')
    entities = []
    for record in records:
        seat_snapshot.validate(record)
        if not {'contour', 'seat_cut'} <= record['features'].keys():
            raise ValueError('Repair required: incomplete generated feature references.')
        if 'tool' in record['features']:
            raise ValueError('Legacy tool/combine seats cannot be edited by this prototype.')
        if record['features'].keys() - FEATURE_ROLES:
            raise ValueError('Repair required: unknown generated feature roles.')
        for role, token in record['features'].items():
            entity = _unique(design, token, role)
            if any(entity == previous for previous in entities):
                raise ValueError('Repair required: generated features are shared between records.')
            entities.append(entity)
    timeline = design.timeline
    indices = sorted(entity.timelineObject.index for entity in entities)
    if (timeline.markerPosition != timeline.count or not indices or indices[0] < 0
            or indices != list(range(indices[0], timeline.count))
            or any(entity.timelineObject.parentGroup is not None for entity in entities)):
        raise ValueError('Only the last complete BearingNest batch without later features or timeline groups can be edited.')
    for record in records:
        for role in ('position', 'body'):
            entity = _unique(design, record['references'][role], role)
            if any(entity == generated for generated in entities):
                raise ValueError('Repair required: placement depends on generated seat geometry.')
    return sorted(entities, key=lambda entity: entity.timelineObject.index, reverse=True)


def update(design, records, values, *, persist, auto_flags=None, bearing=None, profile=None,
           feedback=None, wall_threshold_mm=0):
    values.validate()
    entities = editable_entities(design, records)
    suppressed = []
    succeeded = False
    try:
        # Suppress cuts in reverse order; keep the old geometry available for a
        # failed-preview recovery. Fusion owns rollback of a successful preview.
        for entity in entities:
            if entity.objectType == 'adsk::fusion::Sketch':
                continue
            node = entity.timelineObject
            if node.isSuppressed:
                raise ValueError('Repair required: a generated feature is already suppressed.')
            node.isSuppressed = True
            suppressed.append(node)
        faces = [_unique(design, record['references']['face'], 'face') for record in records]
        if any(face != faces[0] for face in faces):
            raise ValueError('The batch no longer refers to one planar face.')
        positions = [_unique(design, record['references']['position'], 'position') for record in records]
        metadata = {}
        if bearing is not None:
            metadata['bearing'] = bearing
        if profile is not None:
            metadata['profile'] = profile
        if feedback is not None:
            metadata['feedback'] = feedback
        if wall_threshold_mm:
            metadata['wall_threshold_mm'] = wall_threshold_mm
        cuts = seat_geometry.create_seats(design, faces[0], positions, values,
            persist=persist, previous_snapshots=records, auto_flags=auto_flags, **metadata)
        if persist:
            # A failure here aborts the whole execute transaction in the dialog.
            for entity in entities:
                if not entity.isValid or not entity.deleteMe():
                    raise RuntimeError('Could not replace the old batch; the command must roll back.')
        succeeded = True
        return cuts
    finally:
        if not succeeded:
            for node in reversed(suppressed):
                if node.isValid:
                    node.isSuppressed = False
