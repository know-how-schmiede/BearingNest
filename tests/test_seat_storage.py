"""Snapshot behavior and API adapter contracts; not a live Fusion edit proof."""
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / 'Fusion-Add-In/BearingNest'


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        package = ModuleType('snapshot_test')
        package.__path__ = [str(ROOT)]
        self.modules = patch.dict(sys.modules, {'snapshot_test': package})
        self.modules.start()
        self.codec = importlib.import_module('snapshot_test.seat_snapshot')
        self.storage = importlib.import_module('snapshot_test.seat_storage')
        self.bearing = {'D_mm': 22.0, 'd_mm': 8.0, 'B_mm': 7.0,
                        'inner_ring_outside_mm': None}
        self.snapshot = self.codec.create(parameters={'diameter_correction_mm': -0.1},
            bearing=self.bearing, profile={'name': 'Example', 'nozzle_mm': 0.4},
            auto_flags={'relief_depth': True}, references={'face': 'face-token'},
            features={'seat_cut': 'cut-token'})
        self.attributes = {}

        def add(group, name, value):
            attribute = SimpleNamespace(value=value)
            self.attributes[group, name] = attribute
            return attribute

        self.owner = SimpleNamespace(attributes=SimpleNamespace(
            itemByName=lambda group, name: self.attributes.get((group, name)), add=add))

    def tearDown(self):
        self.modules.stop()

    def test_library_changes_do_not_mutate_saved_bearing_or_invent_unknown_values(self):
        self.bearing['D_mm'] = 99
        self.assertEqual(self.snapshot['bearing']['D_mm'], 22)
        self.assertIsNone(self.snapshot['bearing']['inner_ring_outside_mm'])
        self.assertEqual(self.codec.loads(self.codec.dumps(self.snapshot)), self.snapshot)

    def test_updates_preserve_identity_and_replace_same_attribute(self):
        self.storage.save(self.owner, self.snapshot)
        updated = self.codec.revise(self.snapshot, parameters={'diameter_correction_mm': -0.2})
        self.storage.save(self.owner, updated)
        self.assertEqual(len(self.attributes), 1)
        self.assertEqual(updated['seat_id'], self.snapshot['seat_id'])
        self.assertEqual(self.storage.load(self.owner), updated)
        self.assertEqual(self.snapshot['parameters']['diameter_correction_mm'], -0.1)

    def test_bad_snapshots_do_not_overwrite_saved_data(self):
        self.storage.save(self.owner, self.snapshot)
        for changes in ({'schema_version': 2}, {'schema_version': True},
                        {'parameters': {'value': float('nan')}}, {'references': {'face': ''}}):
            with self.assertRaises(ValueError):
                self.storage.save(self.owner, dict(self.snapshot, **changes))
        self.assertEqual(self.storage.load(self.owner), self.snapshot)
        with self.assertRaises(ValueError):
            self.storage.save(self.owner, dict(self.snapshot, seat_id='another-seat'))

    def test_missing_and_split_entities_are_reported_for_repair(self):
        design = SimpleNamespace(findEntityByToken=lambda token: [] if token == 'face-token'
                                 else [object(), object()])
        resolved, repairs = self.storage.resolve_references(design, self.snapshot)
        self.assertEqual(resolved, {})
        self.assertEqual(repairs, {'face': 'missing', 'feature:seat_cut': 'ambiguous'})

    def test_unique_tokens_resolve_and_discovery_uses_entity_attributes(self):
        entity = object()
        design = SimpleNamespace(findEntityByToken=lambda token: [entity],
            findAttributes=lambda group, name: list(self.attributes.values())
                if (group, name) == ('BearingNest', 'seat_snapshot') else [])
        self.storage.save(self.owner, self.snapshot)
        self.assertEqual(len(self.storage.discover(design)), 1)
        resolved, repairs = self.storage.resolve_references(design, self.snapshot)
        self.assertFalse(repairs)
        self.assertIs(resolved['face'], entity)
