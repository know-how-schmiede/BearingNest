"""Catalog provenance, profile overrides and atomic local settings persistence."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / 'Fusion-Add-In/BearingNest'
package = ModuleType('catalog_test')
package.__path__ = [str(ROOT)]
sys.modules['catalog_test'] = package
model = importlib.import_module('catalog_test.catalog_profiles')
parameters = importlib.import_module('catalog_test.seat_parameters')
snapshot = importlib.import_module('catalog_test.seat_snapshot')


class CatalogTests(unittest.TestCase):
    def test_seed_dimensions_are_size_aliases_with_sources_and_unknown_ring_geometry(self):
        records = model.seed_bearings()
        self.assertEqual([(r['designation'], r['d_mm'], r['D_mm'], r['B_mm']) for r in records],
                         [('623', 3, 10, 4), ('624', 4, 13, 5), ('625', 5, 16, 5), ('608', 8, 22, 7)])
        for record in records:
            model.validate_bearing(record)
            self.assertIn('skfmediahub.skf.com', record['source'])
            self.assertIsNone(record['inner_ring_outside_mm'])
            self.assertEqual(record['manufacturer'], '')

    def test_search_matches_all_terms_case_insensitively_and_returns_copies(self):
        records = model.seed_bearings()
        records[0]['manufacturer'] = 'Example Maker'
        found = model.search(records, 'EXAMPLE 623')
        self.assertEqual(len(found), 1)
        found[0]['D_mm'] = 99
        self.assertEqual(records[0]['D_mm'], 10)
        self.assertFalse(model.search(records, 'not-present'))

    def test_only_auto_fields_follow_a_profile_change(self):
        profile = dict(model.DEFAULT_PROFILE, nozzle_mm=0.6, layer_mm=0.3)
        original = {'relief_mm': 1.2, 'fillet_mm': 0.45, 'inner_depth_mm': 0.4, 'correction_mm': -0.15}
        result = model.apply_profile(original, profile, {'relief_mm_auto': True, 'inner_depth_mm_auto': True})
        self.assertAlmostEqual(result['relief_mm'], 1.8)
        self.assertEqual(result['fillet_mm'], 0.45)
        self.assertEqual(result['inner_depth_mm'], 0.6)
        self.assertEqual(result['correction_mm'], -0.15)
        self.assertEqual(original['relief_mm'], 1.2)

    def test_profile_rejects_nonfinite_nonpositive_boolean_and_overflow_dimensions(self):
        for value in (0, -1, float('nan'), float('inf'), True, '0.4'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                model.validate_profile(dict(model.DEFAULT_PROFILE, nozzle_mm=value))
        with self.assertRaises(ValueError):
            model.validate_profile(dict(model.DEFAULT_PROFILE, nozzle_mm=1e308, relief_factor=10))

    def custom(self):
        return dict(model.seed_bearings()[0], id='custom-test', manufacturer='Example',
                    source='Drawing ABC', purchasing_url='https://example.com/short')

    def test_unknown_inner_ring_is_distinct_from_invalid_or_fabricated_values(self):
        record = self.custom()
        model.validate_bearing(record)
        for value in (0, 3, 10, -1, float('nan'), True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                model.validate_bearing(dict(record, inner_ring_outside_mm=value))
        model.validate_bearing(dict(record, inner_ring_outside_mm=6))
        with self.assertRaises(ValueError):
            model.validate_bearing(dict(record, purchasing_url='file:///private'))

    def test_invalid_dimensions_and_missing_metadata_are_rejected(self):
        for change in ({'d_mm': 10}, {'B_mm': 0}, {'designation': ''}, {'source': None}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                model.validate_bearing(dict(self.custom(), **change))

    def test_json_round_trip_keeps_custom_records_and_named_profiles(self):
        data = model.defaults()
        data['bearings'].append(self.custom())
        data['profiles'].append(dict(model.DEFAULT_PROFILE, id='fine', name='Fine', layer_mm=0.1))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'nested' / 'settings.json'
            model.save(data, path)
            self.assertEqual(model.load(path), data)
            self.assertEqual(list(path.parent.glob('*.tmp')), [])
            self.assertEqual(model.load(path.parent / 'missing.json'), model.defaults())

    def test_corrupt_or_future_settings_are_never_silently_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'settings.json'
            for text in ('broken', '{"schema_version":2}', '{"schema_version":true}'):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    model.load(path)
                self.assertEqual(path.read_text(), text)

    def test_failed_validation_or_atomic_replacement_preserves_old_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'settings.json'
            model.save(model.defaults(), path)
            original = path.read_bytes()
            with self.assertRaises(ValueError):
                model.save(dict(model.defaults(), profiles=[]), path)
            with patch.object(model.os, 'replace', side_effect=OSError('locked')):
                with self.assertRaises(OSError):
                    model.save(model.defaults(), path)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(path.parent.glob('*.tmp')), [])

    def test_duplicate_ids_names_and_reserved_seed_ids_are_rejected(self):
        data = model.defaults()
        for records in ([self.custom(), self.custom()], [model.seed_bearings()[0]]):
            with self.assertRaises(ValueError):
                model.validate(dict(data, bearings=records))
        with self.assertRaises(ValueError):
            model.validate(dict(data, profiles=[model.DEFAULT_PROFILE,
                dict(model.DEFAULT_PROFILE, id='other', name=' provisional 0.4 / 0.2 MM ')]))

    def test_bearing_override_tracks_original_dimensions_across_repeated_edits(self):
        seed = model.seed_bearings()[-1]
        values = parameters.SeatParameters(outside_mm=23)
        first = model.bearing_snapshot(seed, values)
        self.assertTrue(first['dimensions_overridden'])
        self.assertEqual(first['catalog_dimensions']['D_mm'], 22)
        self.assertTrue(model.bearing_snapshot(first, values)['dimensions_overridden'])
        self.assertFalse(model.bearing_snapshot(first, parameters.SeatParameters())['dimensions_overridden'])
        self.assertEqual(seed['D_mm'], 22)

    def test_seat_snapshots_keep_effective_dimensions_profile_and_flags_independent(self):
        profile = deepcopy(model.DEFAULT_PROFILE)
        bearing = model.bearing_snapshot(model.seed_bearings()[-1], parameters.SeatParameters())
        record = snapshot.create(parameters=parameters.SeatParameters().snapshot_values(),
            bearing=bearing, profile=profile, auto_flags={'relief_mm_auto': True},
            references={'face': 'token'}, features={'seat_cut': 'cut'})
        profile['nozzle_mm'] = 1
        bearing['D_mm'] = 99
        self.assertEqual(record['profile']['nozzle_mm'], 0.4)
        self.assertEqual(record['bearing']['D_mm'], 22)
        self.assertTrue(snapshot.loads(snapshot.dumps(record))['auto_flags']['relief_mm_auto'])
