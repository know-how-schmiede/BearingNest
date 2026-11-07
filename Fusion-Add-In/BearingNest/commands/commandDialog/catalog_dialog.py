"""Independent catalog editor and shared print-profile controls."""
from copy import deepcopy
from dataclasses import asdict
from html import escape
import math
from pathlib import Path
from uuid import uuid4
import adsk.core
from ... import catalog_profiles as model
from ...strings import TEXT, PROFILE_FIELDS, BEARING_TEXT_FIELDS, PARAMETER_FIELDS, label, source_label
from ...seat_parameters import SeatParameters
from .input_layout import compact_value, compact_control, short_title, tooltip


class CatalogDialog:
    def __init__(self, seat_inputs, settings, seat, catalog):
        self.seat = seat
        self.fields = seat.fields
        self.bearing = None
        self.profile = deepcopy(model.DEFAULT_PROFILE)
        self.last_auto = {}
        self.load_error = None
        try:
            self.data = model.load()
        except Exception as error:
            self.data = model.defaults()
            self.load_error = str(error)
        self.profile = deepcopy(self.data['profiles'][0])
        self.managed_profile = deepcopy(self.profile)
        seat_profile = self._group(seat_inputs, 'seat_profile_group', 'seat_profile_group')
        self._dropdown(seat_profile, 'print_profile', TEXT['print_profile'])
        for field in model.DERIVED:
            self._bool(seat_profile, field + '_auto', TEXT[field + '_auto'], True)
        self._bool(seat_profile, 'profile_reset', TEXT['profile_reset'], button=True)
        self._string(seat_inputs, 'catalog_save_name', TEXT['catalog_save_name'])
        compact_control(seat_inputs, self.fields['catalog_save_name'], TEXT['catalog_save_name'],
            section='catalog_save')
        self._bool(seat_inputs, 'catalog_save', TEXT['catalog_save'], button=True)
        self.save_status = seat_inputs.addTextBoxCommandInput('catalog_save_status', '', '', 2, True)
        self.save_status.isFullWidth = True
        help_field = catalog.addTextBoxCommandInput('catalog_help', '', TEXT['catalog_help'], 4, True)
        help_field.isFullWidth = True
        self._dropdown(catalog, 'catalog_editor', TEXT['catalog_bearing'])
        metadata = self._group(catalog, 'bearing_data_group', 'bearing_data_group')
        for field, title in BEARING_TEXT_FIELDS:
            self._string(metadata, 'custom_' + field, title)
        # Identity is private editor state, never a user-entered deletion target.
        self.editor_bearing = None
        self.editor_profile = deepcopy(model.DEFAULT_PROFILE)
        self.editor_flags = {}
        dimensions = self._group(catalog, 'bearing_dimensions_group', 'bearing_dimensions_group')
        preset = self._group(catalog, 'bearing_preset_group', 'bearing_preset_group', expanded=False)
        for key, title, units, expression in PARAMETER_FIELDS:
            parent = dimensions if key in ('bore_mm', 'outside_mm', 'width_mm') else preset
            self.fields['edit_' + key] = compact_value(parent, 'edit_' + key, title, units,
                expression, help_key=key)
        self._value(dimensions, 'custom_inner_mm', TEXT['custom_inner_mm'], 'mm', 0)
        for key, title, values in (('land_count', TEXT['land_count'], (3, 5, 7, 9)),
                                    ('shaft_mode', TEXT['shaft_mode'], ('Off', 'Through All', 'Blind'))):
            self._dropdown(preset, 'edit_' + key, title)
            for value in values:
                self.fields['edit_' + key].listItems.add(label(str(value)),
                    value == getattr(SeatParameters(), key), '')
        self._bool(preset, 'edit_inner_relief_enabled', TEXT['inner_relief_enabled'])
        self._bool(catalog, 'bearing_save', TEXT['bearing_save'], button=True)
        self._bool(catalog, 'bearing_delete', TEXT['bearing_delete'], button=True)
        self.editor_status = catalog.addTextBoxCommandInput('catalog_editor_status', '', '', 3, True)
        self.editor_status.isFullWidth = True
        settings_root = settings
        settings = self._group(settings_root, 'profiles_group', 'profiles_group')
        self._dropdown(settings, 'settings_profile', TEXT['print_profile'])
        self._string(settings, 'profile_name', TEXT['profile_name'], self.profile['name'])
        for field, title, units in PROFILE_FIELDS:
            self._value(settings, 'profile_' + field, title, units, self.profile[field])
        self._bool(settings, 'profile_save', TEXT['profile_save'], button=True)
        self._bool(settings, 'profile_delete', TEXT['profile_delete'], button=True)
        settings = self._group(settings_root, 'transfer_group', 'transfer_group', expanded=False)
        self._string(settings, 'settings_file', TEXT['settings_file'])
        self._bool(settings, 'settings_import', TEXT['settings_import'], button=True)
        self._bool(settings, 'settings_export', TEXT['settings_export'], button=True)
        self.status = settings_root.addTextBoxCommandInput('catalog_status', '', '', 5, True)
        self.status.isFullWidth = True
        self._choices()
        self._load_editor(None)
        self._suggest()
        self.auto_state = self.flags()
        self._status(TEXT['settings_load_error'].format(error=escape(self.load_error))
                     if self.load_error else TEXT['settings_location'].format(path=escape(str(model.settings_path()))))

    def _string(self, inputs, identity, label, initial=''):
        self.fields[identity] = inputs.addStringValueInput(identity, short_title(identity, label), initial)
        tooltip(self.fields[identity], identity, label)

    def _value(self, inputs, identity, label, units, value):
        self.fields[identity] = compact_value(inputs, identity, label, units,
            f'{value:.12g} {units}'.strip())

    def _bool(self, inputs, identity, label, initial=False, *, button=False):
        self.fields[identity] = inputs.addBoolValueInput(identity, short_title(identity, label), not button, '', initial)
        tooltip(self.fields[identity], identity.removeprefix('edit_'), label)
        if button:
            compact_control(inputs, self.fields[identity], label,
                section='catalog_save' if identity == 'catalog_save' else 'actions')
        elif identity == 'edit_inner_relief_enabled':
            compact_control(inputs, self.fields[identity], label)

    def _group(self, inputs, identity, key, *, expanded=None):
        group = inputs.addGroupCommandInput(identity, TEXT[key])
        group.isExpanded = key == 'bearing_dimensions_group' if expanded is None else expanded
        return group.children

    def _dropdown(self, inputs, identity, label):
        self.fields[identity] = inputs.addDropDownCommandInput(identity, short_title(identity, label),
            adsk.core.DropDownStyles.TextListDropDownStyle)
        tooltip(self.fields[identity], identity.removeprefix('edit_'), label)
        if identity in ('edit_land_count', 'edit_shaft_mode'):
            compact_control(inputs, self.fields[identity], label)

    def _status(self, text):
        self.status.formattedText = text

    def _choices(self):
        self.bearing_choices = {TEXT['manual_bearing']: None}
        records = model.search(model.seed_bearings() + self.data['bearings'],
                               self.fields['catalog_search'].value)
        for record in records:
            label = (f"{record.get('designation', TEXT['saved_bearing_name'])} | {record['d_mm']:.12g} x "
                     f"{record['D_mm']:.12g} x {record['B_mm']:.12g} mm | "
                     f"{record.get('manufacturer') or TEXT['size_alias']} [{record.get('id', 'snapshot')}]")
            self.bearing_choices[label] = record
        if self.bearing and self.bearing not in records:
            # Keep the historical snapshot and the current library entry as
            # separate choices, even when they share a stable catalog identity.
            self.bearing_choices[TEXT['saved_bearing']] = self.bearing
        self._fill('catalog_bearing', self.bearing_choices, self.bearing)
        self.profile_choices = {f"{r['name']} [{r['id']}]": r for r in self.data['profiles']}
        if self.profile not in self.profile_choices.values():
            self.profile_choices[TEXT['saved_profile']] = self.profile
        self._fill('print_profile', self.profile_choices, self.profile)
        self.management_choices = {f"{r['name']} [{r['id']}]": r for r in self.data['profiles']}
        if self.managed_profile not in self.management_choices.values():
            self.management_choices[TEXT['saved_profile']] = self.managed_profile
        self._fill('settings_profile', self.management_choices, self.managed_profile)
        self.editor_choices = {TEXT['new_catalog_bearing']: None}
        for record in model.seed_bearings() + self.data['bearings']:
            title = (f"{record['designation']} | {record['d_mm']:g} x {record['D_mm']:g} x "
                     f"{record['B_mm']:g} mm [{record['id']}]")
            self.editor_choices[title] = record
        selected = next((r for r in self.editor_choices.values()
                         if r and self.editor_bearing and r['id'] == self.editor_bearing['id']), None)
        self._fill('catalog_editor', self.editor_choices, selected)

    def _fill(self, identity, choices, selected):
        items = self.fields[identity].listItems
        items.clear()
        for label, record in choices.items():
            items.add(label, record == selected, '')
            if record == selected:
                setattr(self, '_selected_' + identity, label)

    def flags(self):
        return {field + '_auto': self.fields[field + '_auto'].value for field in model.DERIVED}

    def _suggest(self, only=None, *, apply=True):
        suggestions = model.suggested(self.profile)
        for field in model.DERIVED:
            if apply and (only is None or field == only) and self.fields[field + '_auto'].value:
                value = suggestions[field]
                self.last_auto[field] = value / 10
                self.fields[field].expression = f'{value:.12g} mm'

    def restore(self, record):
        """Use stored snapshots, never today's mutable library/defaults, on reopen."""
        self.bearing = deepcopy(record.get('bearing', {})) or None
        profile = record.get('profile', {})
        try:
            model.validate_profile(profile)
            self.profile = deepcopy(profile)
        except ValueError:
            # Old manual records have no nozzle/layer data: preserve every effective value.
            self.profile = deepcopy(model.DEFAULT_PROFILE)
        for field in model.DERIVED:
            enabled = record.get('auto_flags', {}).get(field + '_auto', False)
            self.fields[field + '_auto'].value = enabled
            self.last_auto[field] = self.fields[field].value if enabled else None
        self.managed_profile = deepcopy(self.profile)
        self._choices()
        self._profile_editor()
        # Display suggestions without applying them to historical geometry.
        self.auto_state = self.flags()
        self._suggest(apply=False)

    def _profile_editor(self):
        self.fields['profile_name'].value = self.managed_profile['name']
        for field, _, units in PROFILE_FIELDS:
            self.fields['profile_' + field].expression = f'{self.managed_profile[field]:.12g} {units}'.strip()

    def _save(self, candidate):
        if self.load_error:
            raise ValueError(TEXT['repair_settings'])
        model.save(candidate)
        self.data = candidate

    def _number(self, identity, length=True):
        field = self.fields[identity]
        if not field.isValidExpression:
            raise ValueError(TEXT['invalid_settings_expression'])
        return field.value * 10 if length else field.value

    @staticmethod
    def _preset(record):
        if record and record.get('seat_preset'):
            preset = deepcopy(record['seat_preset'])
        else:
            values = asdict(SeatParameters(chamfer_mm=0.4))
            if record:
                values.update(bore_mm=record['d_mm'], outside_mm=record['D_mm'],
                              width_mm=record['B_mm'], inner_diameter_mm=record['d_mm'])
            preset = dict(parameters=values, profile=deepcopy(model.DEFAULT_PROFILE),
                          auto_flags={key + '_auto': True for key in model.DERIVED})
        values, flags = preset['parameters'], preset['auto_flags']
        follows_bore = flags.get('inner_diameter_auto',
            math.isclose(values['inner_diameter_mm'], values['bore_mm']))
        ring = (record or {}).get('inner_ring_outside_mm')
        if ring is not None and ring > 0 and follows_bore:
            # A catalog drawing dimension replaces only the automatic placeholder.
            # Do not add uncalibrated clearance or let bore-follow overwrite it.
            values['inner_diameter_mm'] = ring
            flags['inner_diameter_auto'] = False
        return preset

    def _load_editor(self, record):
        self.editor_bearing = deepcopy(record)
        preset = self._preset(record)
        self.editor_profile = preset['profile']
        self.editor_flags = preset['auto_flags']
        values = preset['parameters']
        self._editor_inner_auto = self.editor_flags.get('inner_diameter_auto',
            math.isclose(values['inner_diameter_mm'], values['bore_mm']))
        for key, _ in BEARING_TEXT_FIELDS:
            self.fields['custom_' + key].value = record.get(key, '') if record else ''
        self.fields['custom_inner_mm'].expression = f"{(record or {}).get('inner_ring_outside_mm') or 0:g} mm"
        for key, _, units, _ in PARAMETER_FIELDS:
            self.fields['edit_' + key].expression = f"{preset['parameters'][key]:.12g} {units}"
        for key in ('land_count', 'shaft_mode'):
            items = self.fields['edit_' + key].listItems
            for index in range(items.count):
                item = items.item(index)
                if item.name == label(str(preset['parameters'][key])):
                    item.isSelected = True
                    break
        self.fields['edit_inner_relief_enabled'].value = preset['parameters']['inner_relief_enabled']
        self.fields['bearing_delete'].isEnabled = bool(record and record['id'].startswith('custom-'))
        self.editor_status.formattedText = TEXT['catalog_builtin_copy'] if record and not record['id'].startswith('custom-') else ''

    def _editor_preset(self):
        values = {key: self._number('edit_' + key) if units == 'mm'
                  else math.degrees(self._number('edit_' + key, False))
                  for key, _, units, _ in PARAMETER_FIELDS}
        values.update(land_count=int(self.fields['edit_land_count'].selectedItem.name),
                      shaft_mode=source_label(self.fields['edit_shaft_mode'].selectedItem.name),
                      inner_relief_enabled=self.fields['edit_inner_relief_enabled'].value)
        parameters = SeatParameters(**values)
        parameters.validate()
        parameters.segments()
        flags = deepcopy(self.editor_flags)
        previous = self._preset(self.editor_bearing)['parameters']
        for key in model.DERIVED:
            if not math.isclose(values[key], previous[key], abs_tol=1e-10):
                flags[key + '_auto'] = False
        flags['inner_diameter_auto'] = self._editor_inner_auto
        return dict(parameters=asdict(parameters), profile=deepcopy(self.editor_profile), auto_flags=flags)

    def process(self, identity):
        """Called only from inputChanged with the parent's recursive-event guard set."""
        if identity == 'catalog_save':
            if not self.fields[identity].value:
                return
            self.fields[identity].value = False
            try:
                self._save_parameters()
                self.save_status.formattedText = TEXT['catalog_parameters_saved']
            except Exception as error:
                self.save_status.formattedText = escape(str(error))
        elif identity == 'catalog_search':
            self._choices()
        elif identity == 'catalog_editor':
            selected = self.fields[identity].selectedItem.name
            if selected != self._selected_catalog_editor:
                self._selected_catalog_editor = selected
                self._load_editor(self.editor_choices[selected])
        elif identity == 'edit_bore_mm' and self._editor_inner_auto:
            bore = self.fields[identity]
            if bore.isValidExpression and bore.value > 0:
                self.fields['edit_inner_diameter_mm'].expression = f'{bore.value * 10:.12g} mm'
        elif identity == 'edit_inner_diameter_mm':
            diameter = self.fields[identity]
            bore = self.fields['edit_bore_mm']
            if not diameter.isValidExpression or not bore.isValidExpression or not math.isclose(diameter.value, bore.value):
                self._editor_inner_auto = False
        elif identity == 'catalog_bearing':
            label = self.fields[identity].selectedItem.name
            if label == self._selected_catalog_bearing:
                return  # Fusion can deliver delayed events for programmatic selections.
            self._selected_catalog_bearing = label
            self.bearing = deepcopy(self.bearing_choices[label])
            if self.bearing:
                preset = self._preset(self.bearing)
                self._restore_preset(preset)
                self.fields['catalog_save_name'].value = self.bearing['designation']
                self.save_status.formattedText = ''
        elif identity == 'print_profile':
            label = self.fields[identity].selectedItem.name
            if label == self._selected_print_profile:
                return
            self._selected_print_profile = label
            self.profile = deepcopy(self.profile_choices[label])
            self.managed_profile = deepcopy(self.profile)
            self._choices()
            self._profile_editor()
            self._suggest()
        elif identity == 'settings_profile':
            selected = self.fields[identity].selectedItem.name
            if selected != self._selected_settings_profile:
                self._selected_settings_profile = selected
                self.managed_profile = deepcopy(self.management_choices[selected])
                self._profile_editor()
        elif identity in model.DERIVED:
            field = self.fields[identity]
            if (not field.isValidExpression or self.last_auto.get(identity) is None or
                    not math.isclose(field.value, self.last_auto[identity], rel_tol=0, abs_tol=1e-10)):
                self.fields[identity + '_auto'].value = False
                self.auto_state[identity + '_auto'] = False
        elif identity.endswith('_auto') and identity[:-5] in model.DERIVED:
            enabled = self.fields[identity].value
            if self.auto_state.get(identity) == enabled:
                return
            self.auto_state[identity] = enabled
            if enabled:
                self._suggest(only=identity[:-5])
        elif identity == 'profile_reset' and self.fields[identity].value:
            self.fields[identity].value = False
            for field in model.DERIVED:
                self.fields[field + '_auto'].value = True
            self.auto_state = self.flags()
            self._suggest()
        elif identity in ('bearing_save', 'bearing_delete', 'profile_save',
                          'profile_delete', 'settings_import', 'settings_export') and self.fields[identity].value:
            self.fields[identity].value = False
            try:
                self._action(identity)
                if identity.startswith('bearing_'):
                    self.editor_status.formattedText = TEXT['catalog_action_saved']
                else:
                    self._status(TEXT['settings_saved'])
            except Exception as error:
                if identity.startswith('bearing_'):
                    self.editor_status.formattedText = escape(str(error))
                else:
                    self._status(escape(str(error)))

    def _action(self, identity):
        candidate = deepcopy(self.data)
        if identity == 'bearing_save':
            record = {field: self.fields['custom_' + field].value.strip() for field, _ in BEARING_TEXT_FIELDS}
            existing = self.editor_bearing
            record['id'] = existing['id'] if existing and existing['id'].startswith('custom-') else 'custom-' + str(uuid4())
            for key, field in (('d_mm', 'bore_mm'), ('D_mm', 'outside_mm'), ('B_mm', 'width_mm')):
                record[key] = self._number('edit_' + field)
            inner = self._number('custom_inner_mm')
            record['inner_ring_outside_mm'] = None if inner == 0 else inner
            record['seat_preset'] = self._editor_preset()
            model.validate_bearing(record)
            candidate['bearings'] = [r for r in candidate['bearings'] if r['id'] != record['id']] + [record]
            self._save(candidate)
            self._load_editor(record)
        elif identity == 'bearing_delete':
            identity_to_delete = (self.editor_bearing or {}).get('id')
            if not any(r['id'] == identity_to_delete for r in candidate['bearings']):
                raise ValueError(TEXT['custom_identity_required'])
            candidate['bearings'] = [r for r in candidate['bearings'] if r['id'] != identity_to_delete]
            self._save(candidate)
            self._load_editor(None)
        elif identity == 'profile_save':
            name = self.fields['profile_name'].value.strip()
            existing = next((r for r in candidate['profiles'] if r['name'].casefold() == name.casefold()), None)
            record = dict(id=existing['id'] if existing else 'profile-' + str(uuid4()), name=name)
            for field, _, units in PROFILE_FIELDS:
                record[field] = self._number('profile_' + field, units == 'mm')
            model.validate_profile(record)
            model.suggested(record)
            candidate['profiles'] = [r for r in candidate['profiles'] if r['id'] != record['id']] + [record]
            self._save(candidate)
            self.profile = deepcopy(record)
            self.managed_profile = deepcopy(record)
            self._suggest()
        elif identity == 'profile_delete':
            if not any(r['id'] == self.managed_profile.get('id') for r in candidate['profiles']):
                raise ValueError(TEXT['choose_local_profile'])
            candidate['profiles'] = [r for r in candidate['profiles'] if r['id'] != self.managed_profile['id']]
            self._save(candidate)
            # Deleting a library entry must not recalculate the active seat.
        elif identity in ('settings_import', 'settings_export'):
            filename = self.fields['settings_file'].value.strip()
            path = Path(filename)
            if not filename or not path.is_absolute() or path.suffix.lower() != '.json':
                raise ValueError(TEXT['absolute_json_path'])
            if path.resolve() == model.settings_path().resolve():
                raise ValueError(TEXT['separate_transfer_path'])
            if identity == 'settings_export':
                if path.exists():
                    raise ValueError(TEXT['export_exists'])
                model.save(self.data, path)
                return
            imported = model.load(path) if path.is_file() else None
            if imported is None:
                raise ValueError(TEXT['import_missing'])
            # Merge validated records by identity; never partially import a document.
            for section in ('bearings', 'profiles'):
                merged = {r['id']: r for r in candidate[section]}
                merged.update({r['id']: r for r in imported[section]})
                candidate[section] = list(merged.values())
            self._save(candidate)
            # Existing dialog values and profile snapshots are deliberately unchanged.
        self._choices()

    def _save_parameters(self):
        name = self.fields['catalog_save_name'].value.strip()
        if not name:
            raise ValueError(TEXT['catalog_name_required'])
        preset = self._capture_preset()
        parameters = SeatParameters(**preset['parameters'])
        record = {field: '' for field, _ in BEARING_TEXT_FIELDS}
        if self.bearing:
            record.update(deepcopy(self.bearing))
        # Each explicit save creates a new entry; never overwrite an existing one.
        record.update(id='custom-' + str(uuid4()), designation=name,
                      d_mm=parameters.bore_mm, D_mm=parameters.outside_mm,
                      B_mm=parameters.width_mm)
        record.setdefault('inner_ring_outside_mm', None)
        record.pop('catalog_dimensions', None)
        record.pop('dimensions_overridden', None)
        record['seat_preset'] = preset
        model.validate_bearing(record)
        candidate = deepcopy(self.data)
        candidate['bearings'].append(record)
        self._save(candidate)
        self.bearing = deepcopy(record)
        self.fields['catalog_search'].value = ''
        self._choices()

    def _capture_preset(self):
        values = {key: self._number(key, units == 'mm') if units != 'deg'
                  else math.degrees(self.fields[key].value)
                  for key, _, units, _ in PARAMETER_FIELDS}
        # Validate angle expressions as well as length fields before any write.
        if any(not self.fields[key].isValidExpression for key, *_ in PARAMETER_FIELDS):
            raise ValueError(TEXT['invalid_settings_expression'])
        values.update(land_count=int(self.fields['land_count'].selectedItem.name),
                      shaft_mode=source_label(self.fields['shaft_mode'].selectedItem.name),
                      inner_relief_enabled=self.fields['inner_relief_enabled'].value)
        parameters = SeatParameters(**values)
        parameters.validate()
        parameters.segments()
        flags = dict(self.flags(), inner_diameter_auto=self.seat._inner_diameter_auto)
        return dict(parameters=asdict(parameters), profile=deepcopy(self.profile), auto_flags=flags)

    def _restore_preset(self, preset):
        values = preset['parameters']
        for key, _, units, _ in PARAMETER_FIELDS:
            self.fields[key].expression = f'{values[key]:.12g} {units}'
        for key in ('land_count', 'shaft_mode'):
            items = self.fields[key].listItems
            for index in range(items.count):
                item = items.item(index)
                if item.name == label(str(values[key])):
                    item.isSelected = True
                    break
        self.fields['inner_relief_enabled'].value = values['inner_relief_enabled']
        self.seat._inner_diameter_auto = preset['auto_flags'].get('inner_diameter_auto',
            math.isclose(values['inner_diameter_mm'], values['bore_mm']))
        self.seat._last_auto_inner_value = values['bore_mm'] / 10 if self.seat._inner_diameter_auto else None
        self.restore(dict(bearing=self.bearing, profile=preset['profile'], auto_flags=preset['auto_flags']))
