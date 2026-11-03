"""Prototype Fusion attribute adapter; not wired to geometry creation yet."""
from . import seat_snapshot

GROUP = 'BearingNest'
NAME = 'seat_snapshot'
MAX_BYTES = 2097152


def save(owner, snapshot):
    """Attach to a generated feature, not the Product (findAttributes excludes Product)."""
    value = seat_snapshot.dumps(snapshot)
    if len(value.encode('utf-8')) > MAX_BYTES:
        raise ValueError('Seat snapshot exceeds the Fusion attribute size limit.')
    existing = owner.attributes.itemByName(GROUP, NAME)
    if existing and seat_snapshot.loads(existing.value)['seat_id'] != snapshot['seat_id']:
        raise ValueError('Cannot overwrite a different seat identity.')
    attribute = owner.attributes.add(GROUP, NAME, value)
    if attribute is None:
        raise RuntimeError('Fusion could not save the seat snapshot.')
    return attribute


def discover(design):
    """Return candidate attributes; callers must load and report corrupt records individually."""
    return design.findAttributes(GROUP, NAME)


def load(owner):
    attribute = owner.attributes.itemByName(GROUP, NAME)
    if attribute is None:
        raise ValueError('No BearingNest snapshot is attached to this feature.')
    return seat_snapshot.loads(attribute.value)


def resolve_references(design, snapshot):
    """Require unique matches; missing/split references need repair, never guess a face."""
    seat_snapshot.validate(snapshot)
    resolved, repairs = {}, {}
    for role, token in {**snapshot['references'],
                        **{f'feature:{key}': value for key, value in snapshot['features'].items()}}.items():
        matches = design.findEntityByToken(token)
        if len(matches) == 1:
            resolved[role] = matches[0]
        else:
            repairs[role] = 'missing' if not matches else 'ambiguous'
    return resolved, repairs
