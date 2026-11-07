"""Bounded, in-memory UI timing; report only after the command closes."""
from collections import deque
from contextlib import contextmanager
from functools import wraps
from time import perf_counter


class EventTiming:
    def __init__(self):
        self.stats = {}
        self.recent = deque(maxlen=32)

    def record(self, name, duration, identity=''):
        stats = self.stats.setdefault(name, [0, 0.0, 0.0])
        stats[0] += 1
        stats[1] += duration
        stats[2] = max(stats[2], duration)
        self.recent.append((name, identity, duration))

    @contextmanager
    def measure(self, name):
        start = perf_counter()
        try:
            yield
        finally:
            try:
                self.record(name, perf_counter() - start)
            except Exception:
                pass

    def report(self):
        lines = ['BearingNest UI timing (handler time only; native layout/rollback excluded)']
        lines.append('Nested callback/stage totals overlap; do not add them together.')
        for name, (count, total, maximum) in sorted(self.stats.items()):
            lines.append(f'{name}: count={count}, total={total * 1000:.1f} ms, max={maximum * 1000:.1f} ms')
        lines.append('Recent callbacks (input IDs only, no entered values):')
        lines.extend(f'{name} {identity}: {duration * 1000:.1f} ms'
                     for name, identity, duration in self.recent)
        return '\n'.join(lines)


def timed_event(callback):
    @wraps(callback)
    def measured(self, args):
        start = perf_counter()
        try:
            return callback(self, args)
        finally:
            # Do not let diagnostics mask a callback failure or change transactions.
            try:
                duration = perf_counter() - start
                identity = getattr(getattr(args, 'input', None), 'id', '')
                self.timing.record(callback.__name__, duration, identity)
            except Exception:
                pass
    return measured
