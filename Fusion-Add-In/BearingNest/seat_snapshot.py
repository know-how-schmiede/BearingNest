"""Versioned parameter snapshots, independent of Fusion's API.

Prototype format: values use mm/degrees; schema version is separate from app version.
"""
import json
from uuid import uuid4

SCHEMA_VERSION = 2
SECTIONS = ('parameters', 'bearing', 'profile', 'auto_flags', 'references', 'features')
AUTO_FLAGS = ('relief_mm_auto', 'fillet_mm_auto', 'inner_depth_mm_auto', 'inner_diameter_auto')


def _validate(snapshot, version):
    if not isinstance(snapshot, dict):
        raise ValueError('Seat snapshot must be an object.')
    if type(snapshot.get('schema_version')) is not int or snapshot['schema_version'] != version:
        raise ValueError('Unsupported seat schema version; migration is required.')
    if not isinstance(snapshot.get('seat_id'), str) or not snapshot['seat_id'].strip():
        raise ValueError('Seat identity is missing.')
    if 'batch_id' in snapshot and (not isinstance(snapshot['batch_id'], str) or not snapshot['batch_id'].strip()):
        raise ValueError('Seat batch identity is invalid.')
    for section in SECTIONS:
        if not isinstance(snapshot.get(section), dict):
            raise ValueError(f'Seat section must be an object: {section}')
    if not all(isinstance(value, bool) for value in snapshot['auto_flags'].values()):
        raise ValueError('Auto/manual flags must be Boolean values.')
    for section in ('references', 'features'):
        if not all(isinstance(value, str) and value.strip()
                   for value in snapshot[section].values()):
            raise ValueError(f'{section} must contain nonempty entity tokens.')
    try:
        json.dumps(snapshot, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError('Snapshot values must be finite JSON data.') from error


def validate(snapshot):
    _validate(snapshot, SCHEMA_VERSION)
    if 'batch_id' not in snapshot:
        raise ValueError('Seat batch identity is missing.')
    if any(flag not in snapshot['auto_flags'] for flag in AUTO_FLAGS):
        raise ValueError('Seat auto/manual state is incomplete.')


def migrate(snapshot):
    """Upgrade known legacy data in memory, without rewriting model attributes.

    Never infer a shared batch or recalculate historical values from a profile.
    Unknown fields and unknown bearing dimensions survive unchanged.
    """
    if not isinstance(snapshot, dict):
        raise ValueError('Seat snapshot must be an object.')
    version = snapshot.get('schema_version')
    if type(version) is not int or version not in (1, SCHEMA_VERSION):
        raise ValueError('Unsupported seat schema version; migration is required.')
    _validate(snapshot, version)
    result = json.loads(json.dumps(snapshot, allow_nan=False))
    if version == 1:
        result['schema_version'] = 2
        result.setdefault('batch_id', result['seat_id'])
        result['parameters'].setdefault('chamfer_mm', 0.0)
        for flag in AUTO_FLAGS:
            result['auto_flags'].setdefault(flag, False)
    validate(result)
    return result


def dumps(snapshot):
    validate(snapshot)
    return json.dumps(snapshot, allow_nan=False, sort_keys=True, separators=(',', ':'))


def loads(value):
    return migrate(json.loads(value))


def create(*, parameters, bearing, profile, auto_flags, references, features):
    identity = str(uuid4())
    snapshot = dict(schema_version=SCHEMA_VERSION, seat_id=identity, batch_id=identity,
                    parameters=parameters, bearing=bearing, profile=profile,
                    auto_flags=dict(dict.fromkeys(AUTO_FLAGS, False), **auto_flags),
                    references=references, features=features)
    # Serialize immediately so later edits of source dictionaries cannot change a seat.
    return loads(dumps(snapshot))


def revise(snapshot, **sections):
    validate(snapshot)
    if sections.keys() - set(SECTIONS):
        raise ValueError('Only snapshot sections may be revised; identity and schema stay fixed.')
    return loads(dumps(dict(snapshot, **sections)))
