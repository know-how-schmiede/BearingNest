"""Validated local catalog and print profiles. No Fusion dependency or network access."""
from copy import deepcopy
import json
import math
import os
from pathlib import Path
import tempfile

SCHEMA_VERSION = 1
SOURCE = ('https://cdn.skfmediahub.skf.com/api/public/0901d19680237e2b/'
          'pdf_preview_medium/0901d19680237e2b_pdf_preview_medium.pdf')
DERIVED = {'relief_mm': ('nozzle_mm', 'relief_factor'),
           'fillet_mm': ('nozzle_mm', 'fillet_factor'),
           'inner_depth_mm': ('layer_mm', 'inner_depth_factor')}
DEFAULT_PROFILE = dict(id='default', name='Provisional 0.4 / 0.2 mm', nozzle_mm=0.4,
    layer_mm=0.2, relief_factor=3.0, fillet_factor=1.0, inner_depth_factor=2.0,
    wall_factor=2.0)


def seed_bearings():
    # Size aliases only: the SKF table verifies d/D/B, not ring shoulder geometry.
    return [dict(id='size-' + name, designation=name, d_mm=d, D_mm=D, B_mm=B,
                 inner_ring_outside_mm=None, manufacturer='', part_number='',
                 source=SOURCE + '#page=13', notes='Size alias; dimensions checked 2026-11-04. '
                 'SKF NILOS-Rings, printed page 12. Internal geometry is product-specific.',
                 purchasing_url='')
            for name, d, D, B in [('623', 3, 10, 4), ('624', 4, 13, 5),
                                  ('625', 5, 16, 5), ('608', 8, 22, 7)]]


def _positive(value, name):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value <= 0):
        raise ValueError(f'{name} must be a positive finite number.')


def _text(record, names):
    for name in names:
        if not isinstance(record.get(name), str):
            raise ValueError(f'{name} must be text.')
    for name in ('id', 'name' if 'name' in names else 'designation'):
        if not record[name].strip():
            raise ValueError(f'{name} is required.')


def validate_bearing(record):
    if not isinstance(record, dict):
        raise ValueError('Bearing must be an object.')
    _text(record, ('id', 'designation', 'manufacturer', 'part_number', 'source', 'notes', 'purchasing_url'))
    for name in ('d_mm', 'D_mm', 'B_mm'):
        _positive(record.get(name), name)
    if record['d_mm'] >= record['D_mm']:
        raise ValueError('Bearing bore must be smaller than outside diameter.')
    inner = record.get('inner_ring_outside_mm')
    if inner is not None:
        _positive(inner, 'Inner-ring outside diameter')
        if not record['d_mm'] < inner < record['D_mm']:
            raise ValueError('Inner-ring outside diameter must lie between bore and outside diameter.')
    url = record['purchasing_url']
    if url and not url.startswith(('https://', 'http://')):
        raise ValueError('Purchasing URL must start with https:// or http://.')


def validate_profile(record):
    if not isinstance(record, dict):
        raise ValueError('Print profile must be an object.')
    _text(record, ('id', 'name'))
    for name in ('nozzle_mm', 'layer_mm', 'relief_factor', 'fillet_factor', 'inner_depth_factor', 'wall_factor'):
        _positive(record.get(name), name)
    for base, factor in (*DERIVED.values(), ('nozzle_mm', 'wall_factor')):
        _positive(record[base] * record[factor], 'Derived profile dimension')


def suggested(profile):
    validate_profile(profile)
    result = {field: profile[base] * profile[factor] for field, (base, factor) in DERIVED.items()}
    result['wall_warning_mm'] = profile['nozzle_mm'] * profile['wall_factor']
    for field, value in result.items():
        _positive(value, field)
    return result


def apply_profile(values, profile, auto_flags):
    """Return independent effective values; manual fields survive any profile switch."""
    result = deepcopy(values)
    for field, value in suggested(profile).items():
        if field in DERIVED and auto_flags.get(field + '_auto', False):
            result[field] = value
    return result


def defaults():
    return dict(schema_version=SCHEMA_VERSION, bearings=[], profiles=[deepcopy(DEFAULT_PROFILE)])


def validate(data):
    if not isinstance(data, dict) or type(data.get('schema_version')) is not int or data['schema_version'] != SCHEMA_VERSION:
        raise ValueError('Unsupported settings schema; migration is required.')
    for section, validator in (('bearings', validate_bearing), ('profiles', validate_profile)):
        records = data.get(section)
        if not isinstance(records, list):
            raise ValueError(f'{section} must be a list.')
        identities, names = set(), set()
        for record in records:
            validator(record)
            identity = record['id']
            if identity in identities or (section == 'bearings' and identity.startswith('size-')):
                raise ValueError('Duplicate or reserved record identity.')
            identities.add(identity)
            if section == 'profiles':
                name = record['name'].strip().casefold()
                if name in names:
                    raise ValueError('Print profile names must be unique.')
                names.add(name)
        if section == 'profiles' and not records:
            raise ValueError('Keep at least one print profile.')
    try:
        json.dumps(data, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError('Settings must contain finite JSON data.') from error


def settings_path():
    base = Path(os.environ['APPDATA']) if os.name == 'nt' and os.environ.get('APPDATA') else Path.home() / 'Library' / 'Application Support'
    return base / 'BearingNest' / 'settings.json'


def load(path=None):
    path = Path(path) if path is not None else settings_path()
    if not path.exists():
        return defaults()
    data = json.loads(path.read_text(encoding='utf-8'))
    validate(data)
    return data


def save(data, path=None):
    """Atomic replacement; validation/failing writes leave the original file intact."""
    validate(data)
    text = json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + '\n'
    path = Path(path) if path is not None else settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix=path.name + '.', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def search(bearings, query):
    terms = query.casefold().split()
    return [deepcopy(record) for record in bearings if all(term in ' '.join(
        str(record.get(key, '')) for key in ('designation', 'manufacturer', 'part_number',
                                            'd_mm', 'D_mm', 'B_mm')).casefold() for term in terms)]


def bearing_snapshot(record, parameters):
    result = deepcopy(record) if record else dict(source='manual', inner_ring_outside_mm=None)
    dimensions = dict(d_mm=parameters.bore_mm, D_mm=parameters.outside_mm, B_mm=parameters.width_mm)
    original = result.get('catalog_dimensions', {k: result.get(k) for k in dimensions})
    if record and record.get('id'):
        result['catalog_dimensions'] = deepcopy(original)
    result['dimensions_overridden'] = bool(record and record.get('id') and any(original.get(k) != v for k, v in dimensions.items()))
    result.update(dimensions)
    return result
