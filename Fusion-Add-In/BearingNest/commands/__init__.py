"""Command registry following the owner's Python template."""
from .commandDialog import entry as commandDialog

commands = [commandDialog]


def start():
    for command in commands:
        command.start()


def stop():
    for command in reversed(commands):
        command.stop()
