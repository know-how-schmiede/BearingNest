"""Shared-parameter seat batches and command transaction callbacks."""
from html import escape
import math
import adsk.core
from ...seat_parameters import SeatParameters
from ...strings import TEXT, PARAMETER_FIELDS, label, source_label
from ...seat_feedback import new_feedback


class SeatDialog:
    def __init__(self, inputs, app):
        self.app = app
        self.fields = {}
        self.catalog = None
        self.feedback = new_feedback()
        self._graphics = None
        self._refreshing = False
        self._inner_diameter_auto = True
        self._last_auto_inner_value = None
        self.geometry_error = None
        self._status_text = TEXT['selection_required']
        self._batches = {}
        self._editing_records = None
        self._discovery_errors = []
        chooser = inputs.addDropDownCommandInput('seat_batch', TEXT['edit_batch'],
            adsk.core.DropDownStyles.TextListDropDownStyle)
        chooser.listItems.add(TEXT['new_batch'], True, '')
        self.fields['seat_batch'] = chooser
        self.fields['catalog_search'] = inputs.addStringValueInput('catalog_search', TEXT['catalog_search'], '')
        self.fields['catalog_bearing'] = inputs.addDropDownCommandInput(
            'catalog_bearing', TEXT['catalog_bearing'], adsk.core.DropDownStyles.TextListDropDownStyle)
        if getattr(app, 'activeProduct', None) is not None:
            from adsk import fusion
            from ... import seat_edit
            design = fusion.Design.cast(app.activeProduct)
            if design is not None:
                batches, self._discovery_errors = seat_edit.batches(design)
                for number, records in enumerate(batches, 1):
                    batch_label = TEXT['edit_batch_label'].format(number=number, count=len(records), identity=records[0]['seat_id'][:8])
                    chooser.listItems.add(batch_label, False, '')
                    self._batches[batch_label] = records
        face = inputs.addSelectionInput('seat_face', TEXT['select_face'], TEXT['select_face_prompt'])
        face.addSelectionFilter('PlanarFaces')
        face.setSelectionLimits(1, 1)
        position = inputs.addSelectionInput('seat_position', TEXT['select_position'], TEXT['select_position_prompt'])
        for selection_filter in ('SketchPoints', 'Vertices', 'CircularEdges'):
            position.addSelectionFilter(selection_filter)
        position.setSelectionLimits(1, 0)
        self.fields.update(seat_face=face, seat_position=position)
        self.fields['seat_preview'] = inputs.addBoolValueInput('seat_preview', TEXT['preview'], True, '', True)
        extra_fields = {'bore_mm', 'shaft_allowance_mm', 'blind_depth_mm',
                        'inner_diameter_mm', 'inner_depth_mm'}
        self._add_values(inputs, {field[0] for field in PARAMETER_FIELDS} - extra_fields)
        count = inputs.addDropDownCommandInput('land_count', TEXT['land_count'],
                                               adsk.core.DropDownStyles.TextListDropDownStyle)
        for value in (3, 5, 7, 9):
            count.listItems.add(str(value), value == 5, '')
        self.fields['land_count'] = count
        mode = inputs.addDropDownCommandInput('shaft_mode', TEXT['shaft_mode'],
                                              adsk.core.DropDownStyles.TextListDropDownStyle)
        for name in ('Off', 'Through All', 'Blind'):
            mode.listItems.add(label(name), name == 'Off', '')
        self.fields['shaft_mode'] = mode
        self._add_values(inputs, {'bore_mm', 'shaft_allowance_mm', 'blind_depth_mm'})
        self.fields['inner_relief_enabled'] = inputs.addBoolValueInput(
            'inner_relief_enabled', TEXT['inner_relief_enabled'], True, '', False)
        self._add_values(inputs, {'inner_diameter_mm', 'inner_depth_mm'})
        self._sync_inner_diameter()
        self._refresh_controls()
        self.status = inputs.addTextBoxCommandInput('seat_status', '', TEXT['selection_required'], 4, True)
        self.status.isFullWidth = True
        if self._discovery_errors:
            self._set_status(escape(TEXT['repair_seats'].format(errors='; '.join(self._discovery_errors))))

    def _add_values(self, inputs, identities):
        for identity, label, units, expression in PARAMETER_FIELDS:
            if identity in identities:
                self.fields[identity] = inputs.addValueInput(identity, label, units,
                    adsk.core.ValueInput.createByString(expression))

    def _request(self, *, check_placement=True):
        from ... import seat_geometry
        import adsk.fusion
        face = self.fields['seat_face']
        position = self.fields['seat_position']
        if not self._editing_records and (face.selectionCount != 1 or position.selectionCount < 1):
            raise ValueError(TEXT['selection_required'])
        values = {}
        defaults = SeatParameters()
        for identity, label, units, expression in PARAMETER_FIELDS:
            field = self.fields[identity]
            if not field.isValidExpression:
                if not field.isEnabled:
                    values[identity] = getattr(defaults, identity)
                    continue
                raise ValueError(TEXT['invalid_expression'].format(label=label))
            values[identity] = math.degrees(field.value) if units == 'deg' else field.value * 10.0
        values['land_count'] = int(self.fields['land_count'].selectedItem.name)
        values['shaft_mode'] = source_label(self.fields['shaft_mode'].selectedItem.name)
        values['inner_relief_enabled'] = (values['shaft_mode'] != 'Off'
                                          and self.fields['inner_relief_enabled'].value)
        parameters = SeatParameters(**values)
        parameters.validate()
        design = adsk.fusion.Design.cast(self.app.activeProduct)
        if design is None:
            raise ValueError(TEXT['design_required'])
        if self._editing_records:
            return design, None, self._editing_records, parameters
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

    def _refresh_controls(self):
        if self._refreshing:
            return
        mode = source_label(self.fields['shaft_mode'].selectedItem.name)
        states = {}
        for identity in ('bore_mm', 'shaft_allowance_mm'):
            states[identity] = mode != 'Off'
        states['blind_depth_mm'] = mode == 'Blind'
        states['inner_relief_enabled'] = mode != 'Off'
        enabled = mode != 'Off' and self.fields['inner_relief_enabled'].value
        for identity in ('inner_diameter_mm', 'inner_depth_mm'):
            states[identity] = enabled
        self._refreshing = True
        try:
            for identity, enabled in states.items():
                if getattr(self.fields[identity], 'isEnabled', None) != enabled:
                    self.fields[identity].isEnabled = enabled
        finally:
            self._refreshing = False

    def _sync_inner_diameter(self):
        if not self._inner_diameter_auto:
            return
        bore, diameter = self.fields['bore_mm'], self.fields['inner_diameter_mm']
        if not bore.isValidExpression or bore.value <= 0:
            return
        self._last_auto_inner_value = bore.value
        if not diameter.isValidExpression or not math.isclose(diameter.value, bore.value, rel_tol=0, abs_tol=1e-10):
            was_refreshing = self._refreshing
            self._refreshing = True
            try:
                diameter.expression = f'{bore.value * 10:.12g} mm'
            finally:
                self._refreshing = was_refreshing

    def changed(self, args):
        if self._refreshing or args.input.id not in self.fields:
            return
        try:
            self.clear_feedback()
        except Exception as error:
            self.geometry_error = str(error)
            self._set_status(escape(str(error)))
            return
        self.geometry_error = None
        if self.catalog:
            self._refreshing = True
            try:
                self.catalog.process(args.input.id)
            except Exception as error:
                self.geometry_error = str(error)
                self._set_status(escape(str(error)))
                return
            finally:
                self._refreshing = False
        if args.input.id == 'seat_batch':
            self._editing_records = self._batches.get(self.fields['seat_batch'].selectedItem.name)
            editing = bool(self._editing_records)
            self._refreshing = True
            try:
                for identity in ('seat_face', 'seat_position'):
                    self.fields[identity].isVisible = not editing
                    self.fields[identity].setSelectionLimits(0 if editing else 1,
                        1 if identity == 'seat_face' else 0)
                if editing:
                    from ... import seat_edit
                    values = seat_edit.parameters(self._editing_records[0])
                    for identity, _, units, _ in PARAMETER_FIELDS:
                        self.fields[identity].expression = f'{getattr(values, identity):.12g} {units}'
                    for identity in ('land_count', 'shaft_mode'):
                        items = self.fields[identity].listItems
                        for index in range(items.count):
                            item = items.item(index)
                            if item.name == label(str(getattr(values, identity))):
                                item.isSelected = True
                                break
                    self.fields['inner_relief_enabled'].value = values.inner_relief_enabled
                    self._inner_diameter_auto = self._editing_records[0]['auto_flags'].get(
                        'inner_diameter_auto', math.isclose(values.inner_diameter_mm, values.bore_mm))
                    self._last_auto_inner_value = values.bore_mm / 10 if self._inner_diameter_auto else None
                    if self.catalog:
                        self.catalog.restore(self._editing_records[0])
            except Exception as error:
                self.geometry_error = str(error)
                self._set_status(escape(str(error)))
                return
            finally:
                self._refreshing = False
        if args.input.id == 'inner_diameter_mm':
            diameter = self.fields['inner_diameter_mm']
            if (not diameter.isValidExpression or self._last_auto_inner_value is None
                    or not math.isclose(diameter.value, self._last_auto_inner_value, rel_tol=0, abs_tol=1e-10)):
                self._inner_diameter_auto = False
        if args.input.id in ('bore_mm', 'inner_relief_enabled', 'shaft_mode'):
            self._sync_inner_diameter()
        if (args.input.id == 'seat_face' and self.fields['seat_face'].selectionCount == 1
                and getattr(self.fields['seat_position'], 'isVisible', True)):
            self._refreshing = True
            try:
                self.fields['seat_position'].hasFocus = True
            finally:
                self._refreshing = False
        self._refresh_controls()
        try:
            request = self._request(check_placement=False)
            parameters = request[-1]
            message = TEXT['ready'].format(
                diameter=parameters.contact_mm, depth=parameters.depth_mm, count=len(request[2]))
            if getattr(parameters, 'inner_relief_pending', False):
                message += '<br>' + TEXT['inner_relief_pending']
            self._set_status(message)
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
        self.geometry_error = None
        request = None
        try:
            self.clear_feedback()
            if not self.fields['seat_preview'].value:
                return
            request = self._request(check_placement=False)
            self._apply(request, persist=False)
            parameters = request[-1]
            message = TEXT['preview_ready'].format(
                diameter=parameters.contact_mm, depth=parameters.depth_mm, count=len(request[2]))
            if getattr(parameters, 'inner_relief_pending', False):
                message += '<br>' + TEXT['inner_relief_pending']
            message += self._feedback_message(request)
            self._set_status(message)
        except Exception as error:
            self.geometry_error = str(error)
            message = escape(str(error)).replace('\n', '<br>')
            if request is not None:
                message += self._feedback_message(request)
            self._set_status(message)

    def execute(self, args):
        try:
            self.clear_feedback()
            self._apply(self._request(check_placement=False), persist=True)
        except Exception as error:
            # The template's event wrapper logs exceptions; explicitly abort the Fusion transaction.
            args.executeFailed = True
            args.executeFailedMessage = str(error)
            self._set_status(escape(str(error)))

    def _apply(self, request, *, persist):
        from ... import seat_geometry
        options = {'auto_flags': {'inner_diameter_auto': self._inner_diameter_auto}} if persist else {}
        options['feedback'] = self.feedback
        if self.catalog:
            from ...catalog_profiles import suggested
            options['wall_threshold_mm'] = suggested(self.catalog.profile)['wall_warning_mm']
        if persist and self.catalog:
            from ...catalog_profiles import bearing_snapshot
            options['auto_flags'].update(self.catalog.flags())
            options['bearing'] = bearing_snapshot(self.catalog.bearing, request[-1])
            options['profile'] = self.catalog.profile
        if self._editing_records:
            from ... import seat_edit
            return seat_edit.update(request[0], self._editing_records, request[-1], persist=persist, **options)
        return seat_geometry.create_seats(*request, persist=persist, **options)

    def clear_feedback(self):
        if self._graphics is not None:
            self._graphics.clear()
        self.feedback = new_feedback()

    def _feedback_message(self, request):
        messages = []
        for warnings in self.feedback['warnings'].values():
            for message in warnings:
                if message not in messages:
                    messages.append(message)
        text = ''
        if messages:
            text = '<br><b>' + TEXT['wall_warning_heading'] + '</b><br>' + '<br>'.join(escape(m) for m in messages)
        if self.feedback['issues'] or messages:
            try:
                if self._graphics is None:
                    from ...preview_graphics import PreviewGraphics
                    self._graphics = PreviewGraphics()
                parameters = request[-1]
                radius = parameters.contact_mm / 2 + parameters.relief_mm + parameters.chamfer_mm
                self._graphics.show(request[0], self.feedback, radius)
                text += '<br>' + TEXT['marker_legend']
            except Exception as error:
                text += '<br>' + TEXT['markers_unavailable'].format(error=escape(str(error)))
        return text
