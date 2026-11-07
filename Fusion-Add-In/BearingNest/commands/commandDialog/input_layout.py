"""Shared native numeric rows with room for translated labels."""
import adsk.core
from ...strings import TEXT


def tooltip(field, key, title):
    field.tooltip = title
    field.tooltipDescription = TEXT.get('tip_' + key, title)
    return field


def short_title(key, title):
    return TEXT.get('short_' + key.removeprefix('edit_'), title)


def compact_control(inputs, field, title, *, help_key=None):
    """Place the existing control beside a concise label in equal-width cells."""
    key = help_key or field.id.removeprefix('edit_')
    table = inputs.addTableCommandInput(field.id + '_row', '', 2, '1:1')
    table.isFullWidth = True
    table.minimumVisibleRows = 1
    table.maximumVisibleRows = 1
    table.hasGrid = False
    table.tablePresentationStyle = adsk.core.TablePresentationStyles.transparentBackgroundTablePresentationStyle
    caption = inputs.addStringValueInput(field.id + '_label', '', short_title(key, title))
    caption.isReadOnly = True
    caption.isFullWidth = True
    field.isFullWidth = True
    tooltip(caption, key, title)
    tooltip(field, key, title)
    table.addCommandInput(caption, 0, 0)
    table.addCommandInput(field, 0, 1)
    return field


def compact_value(inputs, identity, title, units, expression, *, help_key=None):
    """Keep the expression editor separate from its label at a 50:50 ratio."""
    field = inputs.addValueInput(identity, title, units,
        adsk.core.ValueInput.createByString(expression))
    return compact_control(inputs, field, title, help_key=help_key)
