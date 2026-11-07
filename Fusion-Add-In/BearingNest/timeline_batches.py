"""Timeline presentation for committed seat batches; previews create no groups."""
from . import seat_storage


def label(records, number, template):
    return template.format(number=number, count=len(records), identity=records[0]['seat_id'][:8])


def group(design, cuts, name):
    records = [seat_storage.load(cut) for cut in cuts]
    nodes = []
    for record in records:
        for token in record['features'].values():
            matches = design.findEntityByToken(token)
            if len(matches) != 1:
                raise RuntimeError('Cannot resolve the complete batch for timeline grouping.')
            nodes.append(matches[0].timelineObject)
    indices = sorted(node.index for node in nodes)
    if (not indices or indices[0] < 0 or len(set(indices)) != len(indices)
            or indices != list(range(indices[0], design.timeline.count))
            or any(node.parentGroup is not None for node in nodes)):
        raise RuntimeError('Cannot group an incomplete or interleaved seat batch.')
    result = design.timeline.timelineGroups.add(indices[0], indices[-1])
    if result is None:
        raise RuntimeError('Fusion could not create the seat timeline group.')
    result.name = name
    result.isCollapsed = True
    return result
