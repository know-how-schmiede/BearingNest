"""Edit transaction orchestration with substitutes; no Fusion kernel acceptance."""
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1] / 'Fusion-Add-In/BearingNest'


class EditTests(unittest.TestCase):
    def setUp(self):
        package = ModuleType('edit_test')
        package.__path__ = [str(ROOT)]
        geometry = ModuleType('edit_test.seat_geometry')
        geometry.create_seats = Mock(return_value=['new cut'])
        self.modules = patch.dict(sys.modules, {'edit_test': package,
            'edit_test.seat_geometry': geometry})
        self.modules.start()
        self.edit = importlib.import_module('edit_test.seat_edit')
        self.geometry = geometry
        self.values = self.edit.SeatParameters(chamfer_mm=0.4)
        self.record = self.edit.seat_snapshot.create(parameters=self.values.snapshot_values(),
            bearing={'D_mm': 22}, profile={'name': 'Saved'}, auto_flags={},
            references={'face': 'face', 'position': 'position', 'body': 'body'},
            features={'contour': 'sketch', 'seat_cut': 'cut'})
        self.record['batch_id'] = 'batch'
        self.sketch = self.entity('Sketch', 3)
        self.cut = self.entity('ExtrudeFeature', 4)
        self.face, self.position, self.body = object(), object(), object()
        self.mapping = {'sketch': [self.sketch], 'cut': [self.cut], 'face': [self.face],
            'position': [self.position], 'body': [self.body]}
        self.design = NS(timeline=NS(markerPosition=5, count=5),
            findEntityByToken=lambda token: self.mapping.get(token, []))

    def entity(self, kind, index):
        return NS(objectType='adsk::fusion::' + kind, isValid=True,
            timelineObject=NS(index=index, identity=index, parentGroup=None, isSuppressed=False, isValid=True),
            deleteMe=Mock(return_value=True))

    def tearDown(self):
        self.modules.stop()

    def test_legacy_snapshot_defaults_to_no_chamfer(self):
        del self.record['parameters']['chamfer_mm']
        self.assertEqual(self.edit.parameters(self.record).chamfer_mm, 0)

    def test_discovery_groups_batches_and_reports_corrupt_records(self):
        other = dict(self.record, seat_id='another')
        self.design.findAttributes = lambda *args: [NS(value=self.edit.seat_snapshot.dumps(value))
            for value in (self.record, other)] + [NS(value='broken')]
        groups, errors = self.edit.batches(self.design)
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]), 2)
        self.assertEqual(len(errors), 1)

    def test_preview_suppresses_old_cuts_but_does_not_delete_or_persist(self):
        def create(*args, **kwargs):
            self.assertTrue(self.cut.timelineObject.isSuppressed)
            self.assertFalse(self.sketch.timelineObject.isSuppressed)
            self.assertFalse(kwargs['persist'])
            self.assertEqual(kwargs['previous_snapshots'], [self.record])
            return ['preview']
        self.geometry.create_seats.side_effect = create
        self.assertEqual(self.edit.update(self.design, [self.record], self.values, persist=False), ['preview'])
        self.cut.deleteMe.assert_not_called()

    def test_failed_preview_restores_original_features(self):
        self.geometry.create_seats.side_effect = ValueError('breakout')
        with self.assertRaisesRegex(ValueError, 'breakout'):
            self.edit.update(self.design, [self.record], self.values, persist=False)
        self.assertFalse(self.cut.timelineObject.isSuppressed)
        self.cut.deleteMe.assert_not_called()

    def test_execute_builds_before_deleting_old_features(self):
        def create(*args, **kwargs):
            self.cut.deleteMe.assert_not_called()
            self.assertTrue(kwargs['persist'])
            return ['new cut']
        self.geometry.create_seats.side_effect = create
        self.edit.update(self.design, [self.record], self.values, persist=True)
        self.cut.deleteMe.assert_called_once()
        self.sketch.deleteMe.assert_called_once()

    def test_downstream_features_and_grouped_timeline_are_rejected_before_writes(self):
        for marker, count, group in ((6, 6, None), (4, 5, None), (5, 5, object())):
            self.design.timeline.markerPosition, self.design.timeline.count = marker, count
            self.cut.timelineObject.parentGroup = group
            with self.assertRaisesRegex(ValueError, 'last complete'):
                self.edit.update(self.design, [self.record], self.values, persist=True)
            self.assertFalse(self.cut.timelineObject.isSuppressed)
            self.geometry.create_seats.assert_not_called()

    def test_missing_and_ambiguous_feature_tokens_require_repair(self):
        for matches in ([], [self.cut, self.cut]):
            self.mapping['cut'] = matches
            with self.assertRaisesRegex(ValueError, 'Repair required'):
                self.edit.update(self.design, [self.record], self.values, persist=False)
            self.geometry.create_seats.assert_not_called()

    def grouped(self, collapsed):
        nodes = [self.sketch.timelineObject, self.cut.timelineObject]
        parent = NS(count=2, parentGroup=None, isCollapsed=collapsed,
                    index=3 if collapsed else -1, item=lambda i: nodes[i],
                    deleteMe=Mock(return_value=True))
        for node in nodes:
            node.parentGroup = parent
            if collapsed:
                node.index = -1
        self.design.timeline.count = self.design.timeline.markerPosition = 4 if collapsed else 5
        return parent

    def test_edit_accepts_collapsed_and_expanded_complete_groups(self):
        for collapsed in (False, True):
            parent = self.grouped(collapsed)
            self.assertEqual(self.edit.editable_entities(self.design, [self.record]),
                             [self.cut, self.sketch])
            self.edit.update(self.design, [self.record], self.values, persist=False)
            parent.deleteMe.assert_not_called()
            self.cut.timelineObject.isSuppressed = False

    def test_execute_ungroups_without_deleting_contents_before_replacement(self):
        parent = self.grouped(True)
        self.edit.update(self.design, [self.record], self.values, persist=True)
        parent.deleteMe.assert_called_once_with(False)
        self.cut.deleteMe.assert_called_once()

    def test_group_with_downstream_features_or_foreign_contents_is_rejected(self):
        parent = self.grouped(True)
        self.design.timeline.count = self.design.timeline.markerPosition = 5
        with self.assertRaisesRegex(ValueError, 'last complete'):
            self.edit.editable_entities(self.design, [self.record])
        self.design.timeline.count = self.design.timeline.markerPosition = 4
        parent.count = 3
        with self.assertRaisesRegex(ValueError, 'last complete'):
            self.edit.editable_entities(self.design, [self.record])

    def test_lost_face_after_suppression_restores_old_cuts(self):
        self.mapping['face'] = []
        with self.assertRaisesRegex(ValueError, 'face'):
            self.edit.update(self.design, [self.record], self.values, persist=False)
        self.assertFalse(self.cut.timelineObject.isSuppressed)

    def test_delete_failure_is_propagated_for_execute_transaction_abort(self):
        self.cut.deleteMe.return_value = False
        with self.assertRaisesRegex(RuntimeError, 'roll back'):
            self.edit.update(self.design, [self.record], self.values, persist=True)

    def test_duplicate_records_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.edit.update(self.design, [self.record, self.record], self.values, persist=True)


if __name__ == '__main__':
    unittest.main()
