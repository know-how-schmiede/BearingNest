"""Coalesce preview requests on Fusion's idle event queue, never inside inputChanged."""
from uuid import uuid4


class DeferredPreview:
    def __init__(self, app, callback, add_handler):
        self.app, self.callback = app, callback
        self.event_id = 'BearingNest.preview.' + str(uuid4())
        self.pending = False
        self.closed = False
        self.handlers = []
        self.event = app.registerCustomEvent(self.event_id)
        if self.event is None:
            raise RuntimeError('Could not register the BearingNest preview queue.')
        try:
            add_handler(self.event, self.flush, local_handlers=self.handlers)
        except Exception:
            app.unregisterCustomEvent(self.event_id)
            self.event = None
            raise

    def request(self):
        if self.closed or self.pending:
            return
        self.pending = True
        try:
            # Verified in the owner's Fusion host: False is returned even when
            # the event is successfully delivered later. The callback, not this
            # unreliable return flag, consumes the pending request.
            self.app.fireCustomEvent(self.event_id)
        except Exception:
            self.pending = False
            raise

    def cancel(self):
        self.pending = False

    def flush(self, args):
        if self.closed or not self.pending:
            return
        self.pending = False
        self.callback(args)

    def close(self):
        self.closed = True
        self.cancel()
        if self.event_id is not None:
            if not self.app.unregisterCustomEvent(self.event_id):
                raise RuntimeError('Could not unregister the BearingNest preview queue.')
            self.event_id = None
            self.event = None
            self.handlers.clear()
