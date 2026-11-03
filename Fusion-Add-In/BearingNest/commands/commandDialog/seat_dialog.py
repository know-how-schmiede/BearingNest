"""Shared-parameter seat batches and command transaction callbacks."""
from html import escape
import math
import adsk.core
from ...seat_parameters import SeatParameters
from ...strings import TEXT, PARAMETER_FIELDS


class SeatDialog:
    def __init__(self, inputs, app):
        self.app = app
        self.fields = {}
        self.geometry_error = None
        self._status_text = TEXT['selection_required']
        face = inputs.addSelectionInput('seat_face', TEXT['select_face'], TEXT['select_face_prompt'])
        face.addSelectionFilter('PlanarFaces')
        face.setSelectionLimits(1, 1)
        position = inputs.addSelectionInput('seat_position', TEXT['select_position'], TEXT['select_position_prompt'])
        for selection_filter in ('SketchPoints', 'Vertices', 'CircularEdges'):
            position.addSelectionFilter(selection_filter)
        position.setSelectionLimits(1, 0)
        self.fields.update(seat_face=face, seat_position=position)
        for identity, label, units, expression in PARAMETER_FIELDS:
            self.fields[identity] = inputs.addValueInput(identity, label, units,
                                                        adsk.core.ValueInput.createByString(expression))
        count = inputs.addDropDownCommandInput('land_count', TEXT['land_count'],
                                               adsk.core.DropDownStyles.TextListDropDownStyle)
        for value in (3, 5, 7, 9):
            count.listItems.add(str(value), value == 5, '')
        self.fields['land_count'] = count
        self.fields['seat_preview'] = inputs.addBoolValueInput('seat_preview', TEXT['preview'], True, '', False)
        self.status = inputs.addTextBoxCommandInput('seat_status', '', TEXT['selection_required'], 3, True)
        self.status.isFullWidth = True

    def _request(self, *, check_placement=True):
        from ... import seat_geometry
        import adsk.fusion
        face = self.fields['seat_face']
        position = self.fields['seat_position']
        if face.selectionCount != 1 or position.selectionCount < 1:
            raise ValueError(TEXT['selection_required'])
        values = {}
        for identity, label, units, expression in PARAMETER_FIELDS:
            field = self.fields[identity]
            if not field.isValidExpression:
                raise ValueError(f'{label}: invalid expression.')
            values[identity] = math.degrees(field.value) if units == 'deg' else field.value * 10.0
        values['land_count'] = int(self.fields['land_count'].selectedItem.name)
        parameters = SeatParameters(**values)
        parameters.validate()
        design = adsk.fusion.Design.cast(self.app.activeProduct)
        if design is None:
            raise ValueError(TEXT['design_required'])
        selected_face = face.selection(0).entity
        selected_positions = [position.selection(index).entity for index in range(position.selectionCount)]
        if check_placement:
            for index, selected_position in enumerate(selected_positions, 1):
                try:
                    seat_geometry.placement(design, selected_face, selected_position)
                except Exception as error:
                    raise ValueError(f'Position {index}: {error}') from error
        return design, selected_face, selected_positions, parameters

    def _set_status(self, text):
        # Writing command inputs invalidates Fusion's dialog state. Avoid redundant writes.
        if text != self._status_text:
            self._status_text = text
            self.status.formattedText = text

    def changed(self, args):
        if args.input.id not in self.fields:
            return
        self.geometry_error = None
        try:
            request = self._request(check_placement=False)
            parameters = request[-1]
            self._set_status(TEXT['ready'].format(
                diameter=parameters.contact_mm, depth=parameters.depth_mm, count=len(request[2])))
        except Exception as error:
            self._set_status(escape(str(error)))

    def validate(self, args):
        # This event must only set areInputsValid. Updating a text box here can
        # invalidate the dialog again, leaving OK disabled despite a "ready" message.
        args.areInputsValid = False
        try:
            # A successful preview has already modified the model. Never recheck
            # placement topology against that temporary cut during dialog validation.
            self._request(check_placement=False)
            if self.geometry_error:
                return
            args.areInputsValid = True
        except Exception:
            # inputChanged and executePreview own error/status text updates.
            pass

    def preview(self, args):
        # Always rebuild in execute, so previews never commit without the seat snapshot.
        args.isValidResult = False
        if not self.fields['seat_preview'].value:
            return
        self.geometry_error = None
        try:
            from ... import seat_geometry
            request = self._request()
            seat_geometry.create_seats(*request, persist=False)
            parameters = request[-1]
            self._set_status(TEXT['preview_ready'].format(
                diameter=parameters.contact_mm, depth=parameters.depth_mm, count=len(request[2])))
        except Exception as error:
            self.geometry_error = str(error)
            self._set_status(escape(str(error)))

    def execute(self, args):
        try:
            from ... import seat_geometry
            seat_geometry.create_seats(*self._request(), persist=True)
        except Exception as error:
            # The template's event wrapper logs exceptions; explicitly abort the Fusion transaction.
            args.executeFailed = True
            args.executeFailedMessage = str(error)
            self._set_status(escape(str(error)))
