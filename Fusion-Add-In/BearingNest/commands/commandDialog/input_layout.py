"""Shared native numeric rows with room for translated labels."""
import adsk.core
from ...strings import TEXT


def tooltip(field, key, title):
    field.tooltip = title
    field.tooltipDescription = TEXT.get('tip_' + key, title)
    return field


def short_title(key, title):
    return TEXT.get('short_' + key.removeprefix('edit_'), title)


def compact_control(inputs, field, title, *, help_key=None, section='values', show_label=True):
    """Give labels and controls equal column widths."""
    key = help_key or field.id.removeprefix('edit_')
    parent = field.parentCommandInput
    # Separate sections keep controls on either side of selections/status/groups
    # in their original order rather than appending them to the header table.
    table_id = (parent.id if parent else 'root') + '_' + section
    table = inputs.itemById(table_id)
    if table is None:
        # One native layout container per group, rather than one per value.
        table = inputs.addTableCommandInput(table_id, '', 2, '1:1')
        table.isFullWidth = True
        table.minimumVisibleRows = 1
        table.hasGrid = False
        table.tablePresentationStyle = adsk.core.TablePresentationStyles.transparentBackgroundTablePresentationStyle
    row = table.rowCount
    table.maximumVisibleRows = row + 1
    # All rows are known at construction; avoid a flexible table-height range.
    table.minimumVisibleRows = row + 1
    caption = inputs.addStringValueInput(field.id + '_label', '',
        short_title(key, title) if show_label else '')
    caption.isReadOnly = True
    caption.isFullWidth = True
    field.isFullWidth = True
    tooltip(caption, key, title)
    tooltip(field, key, title)
    table.addCommandInput(caption, row, 0)
    table.addCommandInput(field, row, 1)
    return field


def compact_value(inputs, identity, title, units, expression, *, help_key=None):
    """Keep the expression editor separate from its label at a 50:50 ratio."""
    field = inputs.addValueInput(identity, title, units,
        adsk.core.ValueInput.createByString(expression))
    return compact_control(inputs, field, title, help_key=help_key)
