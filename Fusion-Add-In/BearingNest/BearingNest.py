"""Fusion entry points, preserving the owner's command registry lifecycle."""
from . import commands
from .lib import fusionAddInUtils as futil


def run(context):
    try:
        commands.start()
    except Exception:
        futil.handle_error('run', show_message_box=True)


def stop(context):
    try:
        commands.stop()
    except Exception:
        futil.handle_error('stop', show_message_box=True)
    finally:
        futil.clear_handlers()
