"""Catalog/profile controls in the existing three-tab command."""
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


class CatalogDialog:
    def __init__(self, seat_inputs, settings, seat):
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
        self._string(seat_inputs, 'catalog_save_name', TEXT['catalog_save_name'])
        self.fields['catalog_save'] = seat_inputs.addBoolValueInput(
            'catalog_save', TEXT['catalog_save'], False, '', False)
        self.save_status = seat_inputs.addTextBoxCommandInput('catalog_save_status', '', '', 2, True)
        self.save_status.isFullWidth = True
        self._dropdown(settings, 'print_profile', TEXT['print_profile'])
        for field in model.DERIVED:
            self._bool(settings, field + '_auto', TEXT[field + '_auto'], True)
        self._bool(settings, 'profile_reset', TEXT['profile_reset'])
        self._string(settings, 'custom_id', TEXT['custom_id'])
        for field, label in BEARING_TEXT_FIELDS:
            self._string(settings, 'custom_' + field, label)
        self._value(settings, 'custom_inner_mm', TEXT['custom_inner_mm'], 'mm', 0)
        self._bool(settings, 'bearing_load', TEXT['bearing_load'])
        self._bool(settings, 'bearing_save', TEXT['bearing_save'])
        self._bool(settings, 'bearing_delete', TEXT['bearing_delete'])
        self._string(settings, 'profile_name', TEXT['profile_name'], self.profile['name'])
        for field, label, units in PROFILE_FIELDS:
            self._value(settings, 'profile_' + field, label, units, self.profile[field])
        self._bool(settings, 'profile_save', TEXT['profile_save'])
        self._bool(settings, 'profile_delete', TEXT['profile_delete'])
        self._string(settings, 'settings_file', TEXT['settings_file'])
        self._bool(settings, 'settings_import', TEXT['settings_import'])
        self._bool(settings, 'settings_export', TEXT['settings_export'])
        self.status = settings.addTextBoxCommandInput('catalog_status', '', '', 5, True)
        self.status.isFullWidth = True
        self._choices()
        self._suggest()
        self.auto_state = self.flags()
        self._status(TEXT['settings_load_error'].format(error=escape(self.load_error))
                     if self.load_error else TEXT['settings_location'].format(path=escape(str(model.settings_path()))))

    def _string(self, inputs, identity, label, initial=''):
        self.fields[identity] = inputs.addStringValueInput(identity, label, initial)

    def _value(self, inputs, identity, label, units, value):
        self.fields[identity] = inputs.addValueInput(identity, label, units,
            adsk.core.ValueInput.createByString(f'{value:.12g} {units}'.strip()))

    def _bool(self, inputs, identity, label, initial=False):
        self.fields[identity] = inputs.addBoolValueInput(identity, label, True, '', initial)

    def _dropdown(self, inputs, identity, label):
        self.fields[identity] = inputs.addDropDownCommandInput(identity, label,
            adsk.core.DropDownStyles.TextListDropDownStyle)

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
        self._choices()
        self._profile_editor()
        # Display suggestions without applying them to historical geometry.
        self.auto_state = self.flags()
        self._suggest(apply=False)

    def _profile_editor(self):
        self.fields['profile_name'].value = self.profile['name']
        for field, _, units in PROFILE_FIELDS:
            self.fields['profile_' + field].expression = f'{self.profile[field]:.12g} {units}'.strip()

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
        elif identity == 'catalog_bearing':
            label = self.fields[identity].selectedItem.name
            if label == self._selected_catalog_bearing:
                return  # Fusion can deliver delayed events for programmatic selections.
            self._selected_catalog_bearing = label
            self.bearing = deepcopy(self.bearing_choices[label])
            if self.bearing:
                preset = self.bearing.get('seat_preset')
                if preset is None:
                    # Dimension-only records must not inherit the last bearing's
                    # shaft, relief, fit or print settings.
                    values = asdict(SeatParameters())
                    values.update(bore_mm=self.bearing['d_mm'], outside_mm=self.bearing['D_mm'],
                                  width_mm=self.bearing['B_mm'], inner_diameter_mm=self.bearing['d_mm'],
                                  chamfer_mm=0.4)
                    preset = dict(parameters=values, profile=deepcopy(model.DEFAULT_PROFILE),
                                  auto_flags={key + '_auto': True for key in model.DERIVED})
                self._restore_preset(preset)
                self.fields['catalog_save_name'].value = self.bearing['designation']
                self.fields['custom_id'].value = self.bearing['id'] if self.bearing['id'].startswith('custom-') else ''
                for field, _ in BEARING_TEXT_FIELDS:
                    self.fields['custom_' + field].value = self.bearing.get(field, '')
                self.fields['custom_inner_mm'].expression = f"{self.bearing.get('inner_ring_outside_mm') or 0:.12g} mm"
                self.save_status.formattedText = ''
        elif identity == 'print_profile':
            label = self.fields[identity].selectedItem.name
            if label == self._selected_print_profile:
                return
            self._selected_print_profile = label
            self.profile = deepcopy(self.profile_choices[label])
            self._profile_editor()
            self._suggest()
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
        elif identity in ('bearing_load', 'bearing_save', 'bearing_delete', 'profile_save',
                          'profile_delete', 'settings_import', 'settings_export') and self.fields[identity].value:
            self.fields[identity].value = False
            try:
                self._action(identity)
                self._status(TEXT['settings_saved'])
            except Exception as error:
                self._status(escape(str(error)))

    def _action(self, identity):
        candidate = deepcopy(self.data)
        if identity == 'bearing_load':
            if not self.bearing:
                raise ValueError(TEXT['choose_bearing'])
            record = self.bearing
            # Built-ins are copied to new custom identities rather than overwritten.
            self.fields['custom_id'].value = record.get('id', '') if record.get('id', '').startswith('custom-') else ''
            for field, _ in BEARING_TEXT_FIELDS:
                self.fields['custom_' + field].value = record.get(field, '')
            self.fields['custom_inner_mm'].expression = f"{record.get('inner_ring_outside_mm') or 0:.12g} mm"
            return
        if identity == 'bearing_save':
            record = {field: self.fields['custom_' + field].value.strip() for field, _ in BEARING_TEXT_FIELDS}
            record['id'] = self.fields['custom_id'].value.strip() or 'custom-' + str(uuid4())
            if not record['id'].startswith('custom-'):
                raise ValueError(TEXT['custom_identity_required'])
            for key, field in (('d_mm', 'bore_mm'), ('D_mm', 'outside_mm'), ('B_mm', 'width_mm')):
                record[key] = self._number(field)
            inner = self._number('custom_inner_mm')
            record['inner_ring_outside_mm'] = None if inner == 0 else inner
            record['seat_preset'] = self._capture_preset()
            model.validate_bearing(record)
            candidate['bearings'] = [r for r in candidate['bearings'] if r['id'] != record['id']] + [record]
            self._save(candidate)
            self.bearing = deepcopy(record)
            self.fields['custom_id'].value = record['id']
        elif identity == 'bearing_delete':
            identity_to_delete = self.fields['custom_id'].value.strip()
            if not any(r['id'] == identity_to_delete for r in candidate['bearings']):
                raise ValueError(TEXT['custom_identity_required'])
            candidate['bearings'] = [r for r in candidate['bearings'] if r['id'] != identity_to_delete]
            self._save(candidate)
            # Retain this dialog's detached snapshot, including during an edit.
            self.fields['custom_id'].value = ''
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
            self._suggest()
        elif identity == 'profile_delete':
            if not any(r['id'] == self.profile.get('id') for r in candidate['profiles']):
                raise ValueError(TEXT['choose_local_profile'])
            candidate['profiles'] = [r for r in candidate['profiles'] if r['id'] != self.profile['id']]
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
