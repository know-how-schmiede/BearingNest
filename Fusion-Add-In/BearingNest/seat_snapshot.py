"""Versioned parameter snapshots, independent of Fusion's API.

Prototype format: values use mm/degrees; schema version is separate from app version.
"""
import json
from uuid import uuid4

SCHEMA_VERSION = 1
SECTIONS = ('parameters', 'bearing', 'profile', 'auto_flags', 'references', 'features')


def validate(snapshot):
    if not isinstance(snapshot, dict):
        raise ValueError('Seat snapshot must be an object.')
    if type(snapshot.get('schema_version')) is not int or snapshot['schema_version'] != SCHEMA_VERSION:
        raise ValueError('Unsupported seat schema version; migration is required.')
    if not isinstance(snapshot.get('seat_id'), str) or not snapshot['seat_id'].strip():
        raise ValueError('Seat identity is missing.')
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


def dumps(snapshot):
    validate(snapshot)
    return json.dumps(snapshot, allow_nan=False, sort_keys=True, separators=(',', ':'))


def loads(value):
    snapshot = json.loads(value)
    validate(snapshot)
    return snapshot


def create(*, parameters, bearing, profile, auto_flags, references, features):
    snapshot = dict(schema_version=SCHEMA_VERSION, seat_id=str(uuid4()),
                    parameters=parameters, bearing=bearing, profile=profile,
                    auto_flags=auto_flags, references=references, features=features)
    # Serialize immediately so later edits of source dictionaries cannot change a seat.
    return loads(dumps(snapshot))


def revise(snapshot, **sections):
    validate(snapshot)
    if sections.keys() - set(SECTIONS):
        raise ValueError('Only snapshot sections may be revised; identity and schema stay fixed.')
    return loads(dumps(dict(snapshot, **sections)))
