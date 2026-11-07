"""Atomic rebuilding of an owned BearingNest timeline suffix.

No marker moves, arbitrary downstream feature edits or guessed reference repairs.
Fusion owns successful preview rollback and the complete execute transaction.
"""
from . import seat_edit, seat_geometry, timeline_batches
from .strings import TEXT


def _span(entities):
    nodes = [entity.timelineObject for entity in entities]
    parent = nodes[0].parentGroup
    if parent is not None and parent.isCollapsed:
        return parent.index, parent.index
    indices = [node.index for node in nodes]
    return min(indices), max(indices)


def plan(design, records, choices):
    """Prove complete ownership of the affected tail before changing the model."""
    entities = seat_edit.editable_entities(design, records, require_tail=False)
    first, last = _span(entities)
    identity = records[0]['batch_id']
    selected_name = next((name for name, batch in choices.items()
                          if batch[0]['batch_id'] == identity), None)
    if selected_name is None:
        raise ValueError(TEXT['edit_chain_incomplete'])
    result = [(first, last, selected_name, records, entities)]
    if last == design.timeline.count - 1:
        return result
    # All candidates must resolve uniquely to establish their position and
    # prove ownership of the entire suffix without guessing timeline order.
    for name, batch in choices.items():
        if batch[0]['batch_id'] == identity:
            continue
        try:
            candidate = seat_edit.editable_entities(design, batch, require_tail=False)
        except Exception:
            # Without a valid span we cannot prove whether this is a later
            # batch. Fail closed instead of hiding a damaged downstream batch.
            raise ValueError(TEXT['edit_chain_incomplete']) from None
        start, end = _span(candidate)
        if start > first:
            result.append((start, end, name, batch, candidate))
    result.sort(key=lambda item: item[0])
    cursor = first
    owned = []
    for start, end, _, _, batch_entities in result:
        if start != cursor:
            raise ValueError(TEXT['edit_chain_foreign'])
        for entity in batch_entities:
            if any(entity == previous for previous in owned):
                raise ValueError(TEXT['edit_chain_incomplete'])
            owned.append(entity)
        cursor = end + 1
    if cursor != design.timeline.count:
        raise ValueError(TEXT['edit_chain_foreign'])
    # Placement must not use a generated sketch/edge from the suffix being
    # replaced. Body and face references are checked again after suppression.
    for _, _, _, batch, _ in result:
        for record in batch:
            point = seat_edit._unique(design, record['references']['position'], 'position')
            source = getattr(point, 'parentSketch', point)
            if any(source == entity for entity in owned):
                raise ValueError(TEXT['edit_chain_reference'])
    return result


def update(design, records, values, *, persist, batch_choices, **options):
    values.validate()
    chain = plan(design, records, batch_choices)
    if len(chain) == 1:
        return seat_edit.update(design, records, values, persist=persist, **options)
    suppressed, generated, fills, replacements = [], [], [], []
    succeeded = False
    try:
        # Suppress all old cuts from latest to earliest before any new cut.
        for _, _, _, _, entities in reversed(chain):
            for entity in entities:
                if entity.objectType == 'adsk::fusion::Sketch':
                    continue
                node = entity.timelineObject
                if node.isSuppressed:
                    raise ValueError(TEXT['edit_chain_suppressed'])
                node.isSuppressed = True
                suppressed.append(node)
        baselines = []
        for _, _, _, batch, _ in chain:
            references = seat_edit._resolve_all(design, [
                (record['references'].get(role, ''), f'{record["seat_id"][:8]} / {role}')
                for record in batch for role in ('face', 'position', 'body')])
            faces, positions, bodies = references[::3], references[1::3], references[2::3]
            if (any(face != faces[0] for face in faces)
                    or any(face.body != body for face, body in zip(faces, bodies))):
                raise ValueError(TEXT['edit_chain_reference'])
            # Capture tokens before replacement topology changes, just as for
            # new-seat previews. Never retain tokens from a temporary cut face.
            baselines.append((faces[0].entityToken, [point.entityToken for point in positions]))
            for point in positions:
                sketch = getattr(point, 'parentSketch', None)
                if sketch is not None and not any(sketch == old for old, _ in fills):
                    fills.append((sketch, sketch.areProfilesShown))
        for index, (_, _, name, batch, _) in enumerate(chain):
            face_token, position_tokens = baselines[index]
            references = seat_edit._resolve_all(design,
                [(face_token, 'face')] + [(token, 'position') for token in position_tokens])
            metadata = options if index == 0 else {'preserve_metadata': True}
            try:
                cuts = seat_geometry.create_seats(design, references[0], references[1:],
                    values if index == 0 else seat_edit.parameters(batch[0]), persist=persist,
                    previous_snapshots=batch, generated_entities=generated, **metadata)
            except Exception as error:
                raise ValueError(TEXT['edit_chain_failed'].format(name=name, error=error)) from error
            replacements.append(cuts)
        if persist:
            # Only after every replacement passed preflight and creation may
            # original groups/features be removed. Execute failure rolls back all.
            for _, _, _, _, entities in reversed(chain):
                parent = entities[0].timelineObject.parentGroup
                if parent is not None and not parent.deleteMe(False):
                    raise RuntimeError(TEXT['edit_chain_delete'])
                for entity in entities:
                    if not entity.isValid or not entity.deleteMe():
                        raise RuntimeError(TEXT['edit_chain_delete'])
            seat_geometry.verify_rebuild(design, generated)
            # The caller groups the selected batch. Later batches retain their
            # chooser names and remain separate, in their original order.
            for item, cuts in zip(chain[1:], replacements[1:]):
                timeline_batches.group(design, cuts, item[2])
        succeeded = True
        return replacements[0]
    finally:
        if not succeeded:
            failures = []
            for entity in reversed(generated):
                try:
                    if entity.isValid and not entity.deleteMe():
                        failures.append('new feature')
                except Exception:
                    failures.append('new feature')
            for sketch, original in fills:
                try:
                    if sketch.isValid:
                        sketch.areProfilesShown = original
                except Exception:
                    failures.append('profile display')
            for node in reversed(suppressed):
                try:
                    if node.isValid:
                        node.isSuppressed = False
                except Exception:
                    failures.append('original suppression')
            if failures:
                raise RuntimeError(TEXT['edit_chain_cleanup'])
