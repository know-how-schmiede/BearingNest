"""Earlier-batch transaction orchestration; no Fusion geometry/kernel proof."""
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1] / 'Fusion-Add-In/BearingNest'


class ChainTests(unittest.TestCase):
    def setUp(self):
        package = ModuleType('chain_test')
        package.__path__ = [str(ROOT)]
        self.geometry = ModuleType('chain_test.seat_geometry')
        self.geometry.create_seats = Mock(side_effect=self.create)
        self.geometry.verify_rebuild = Mock()
        self.modules = patch.dict(sys.modules, {'chain_test': package,
                                               'chain_test.seat_geometry': self.geometry})
        self.modules.start()
        self.chain = importlib.import_module('chain_test.seat_chain')
        self.edit = self.chain.seat_edit
        self.group_patch = patch.object(self.chain.timeline_batches, 'group')
        self.group = self.group_patch.start()
        self.trace, self.mapping, self.originals, self.records = [], {}, [], []
        self.body = NS(entityToken='body')
        self.mapping['body'] = [self.body]
        self.fills = NS(isValid=True, areProfilesShown=True, identity='source')
        for number in range(2):
            face = NS(entityToken=f'face{number}', body=self.body)
            point = NS(entityToken=f'point{number}', parentSketch=self.fills)
            self.mapping[face.entityToken], self.mapping[point.entityToken] = [face], [point]
            sketch = self.entity(f'sketch{number}', 3 + 2 * number, sketch=True)
            cut = self.entity(f'cut{number}', 4 + 2 * number)
            self.originals.append((sketch, cut))
            self.mapping[f'sketch{number}'], self.mapping[f'cut{number}'] = [sketch], [cut]
            record = self.edit.seat_snapshot.create(
                parameters=self.edit.SeatParameters(width_mm=7 + number).snapshot_values(),
                bearing={'D_mm': 22, 'source': f'drawing{number}'},
                profile={'name': f'saved{number}'}, auto_flags={'relief_mm_auto': bool(number)},
                references={'face': face.entityToken, 'position': point.entityToken, 'body': 'body'},
                features={'contour': f'sketch{number}', 'seat_cut': f'cut{number}'})
            self.records.append([record])
        self.choices = {'Second': self.records[1], 'First': self.records[0]}
        self.design = NS(timeline=NS(markerPosition=7, count=7),
                         findEntityByToken=lambda token: self.mapping.get(token, []))
        self.values = self.edit.SeatParameters(width_mm=6, chamfer_mm=0.4)
        self.new = []

    def tearDown(self):
        self.group_patch.stop()
        self.modules.stop()

    def entity(self, name, index, *, sketch=False):
        entity = NS(isValid=True, name=name,
            objectType='adsk::fusion::Sketch' if sketch else 'adsk::fusion::ExtrudeFeature',
            timelineObject=NS(identity=name, index=index, parentGroup=None,
                              isSuppressed=False, isValid=True))
        def delete():
            self.trace.append('delete ' + name)
            entity.isValid = False
            entity.timelineObject.isValid = False
            return True
        entity.deleteMe = Mock(side_effect=delete)
        return entity

    def create(self, design, face, positions, values, **kwargs):
        self.assertTrue(all(cut.timelineObject.isSuppressed for _, cut in self.originals))
        self.assertTrue(all(entity.isValid for batch in self.originals for entity in batch))
        number = len(self.new)
        self.trace.append(f'build {number}')
        new = self.entity(f'new{number}', 7 + number)
        self.new.append(new)
        kwargs['generated_entities'].append(new)
        if kwargs['persist']:
            self.fills.areProfilesShown = False
        return [new]

    def update(self, **kwargs):
        return self.edit.update(self.design, self.records[0], self.values,
            batch_choices=self.choices, **kwargs)

    def test_preview_rebuilds_in_timeline_order_and_keeps_following_values(self):
        result = self.update(persist=False, bearing={'source': 'changed'}, auto_flags={'fillet_mm_auto': True})
        calls = self.geometry.create_seats.call_args_list
        self.assertEqual(calls[0].args[3], self.values)
        self.assertEqual(calls[1].args[3].width_mm, 8)
        self.assertEqual(calls[1].kwargs['previous_snapshots'], self.records[1])
        self.assertNotIn('bearing', calls[1].kwargs)
        self.assertNotIn('auto_flags', calls[1].kwargs)
        self.assertTrue(calls[1].kwargs['preserve_metadata'])
        self.assertEqual(result, [self.new[0]])
        self.assertEqual(self.trace, ['build 0', 'build 1'])
        self.group.assert_not_called()
        self.geometry.verify_rebuild.assert_not_called()

    def test_apply_builds_all_before_deleting_originals_and_keeps_group_names(self):
        self.update(persist=True)
        self.assertEqual(self.trace, ['build 0', 'build 1', 'delete cut1',
                                     'delete sketch1', 'delete cut0', 'delete sketch0'])
        self.geometry.verify_rebuild.assert_called_once_with(self.design, self.new)
        self.group.assert_called_once_with(self.design, [self.new[1]], 'Second')

    def test_later_rebuild_failure_cleans_new_features_and_restores_originals(self):
        def fail(*args, **kwargs):
            if self.new:
                raise ValueError('overlap')
            return self.create(*args, **kwargs)
        self.geometry.create_seats.side_effect = fail
        with self.assertRaisesRegex(ValueError, 'Second.*overlap'):
            self.update(persist=True)
        self.assertFalse(self.new[0].isValid)
        self.assertTrue(self.fills.areProfilesShown)
        for sketch, cut in self.originals:
            self.assertTrue(sketch.isValid)
            self.assertTrue(cut.isValid)
            self.assertFalse(cut.timelineObject.isSuppressed)
            cut.deleteMe.assert_not_called()
        self.group.assert_not_called()

    def test_foreign_tail_or_interleaved_operation_is_rejected_before_writes(self):
        for count, start in ((8, 5), (8, 6)):
            self.design.timeline.count = self.design.timeline.markerPosition = count
            self.originals[1][0].timelineObject.index = start
            self.originals[1][1].timelineObject.index = start + 1
            with self.assertRaisesRegex(ValueError, 'Unrelated operations'):
                self.update(persist=False)
            self.geometry.create_seats.assert_not_called()
            self.assertFalse(self.originals[0][1].timelineObject.isSuppressed)

    def test_missing_later_feature_is_rejected_before_suppression(self):
        self.mapping['cut1'] = []
        with self.assertRaisesRegex(ValueError, 'complete sequence'):
            self.update(persist=False)
        self.assertFalse(self.originals[0][1].timelineObject.isSuppressed)
        self.geometry.create_seats.assert_not_called()

    def test_already_suppressed_later_cut_blocks_update(self):
        self.originals[1][1].timelineObject.isSuppressed = True
        with self.assertRaisesRegex(ValueError, 'already suppressed'):
            self.update(persist=False)
        self.assertFalse(self.originals[0][1].timelineObject.isSuppressed)
        self.assertTrue(self.originals[1][1].timelineObject.isSuppressed)
        self.geometry.create_seats.assert_not_called()

    def test_missing_restored_face_recovers_all_original_suppression(self):
        self.mapping['face1'] = []
        with self.assertRaisesRegex(ValueError, 'face'):
            self.update(persist=False)
        self.assertTrue(all(not cut.timelineObject.isSuppressed for _, cut in self.originals))
        self.geometry.create_seats.assert_not_called()

    def test_reference_to_generated_sketch_is_rejected(self):
        self.mapping['point1'][0].parentSketch = self.originals[0][0]
        with self.assertRaisesRegex(ValueError, 'placement reference'):
            self.update(persist=False)
        self.geometry.create_seats.assert_not_called()

    def test_delete_failure_requires_execute_rollback(self):
        self.originals[1][1].deleteMe.side_effect = None
        self.originals[1][1].deleteMe.return_value = False
        with self.assertRaisesRegex(RuntimeError, 'roll back'):
            self.update(persist=True)
        self.geometry.verify_rebuild.assert_not_called()

    def test_recompute_failure_requires_execute_rollback(self):
        self.geometry.verify_rebuild.side_effect = RuntimeError('unhealthy replacement')
        with self.assertRaisesRegex(RuntimeError, 'unhealthy replacement'):
            self.update(persist=True)
        self.group.assert_not_called()

    def test_plan_handles_collapsed_and_expanded_groups_without_layout_writes(self):
        for number, (sketch, cut) in enumerate(self.originals):
            nodes = [sketch.timelineObject, cut.timelineObject]
            parent = NS(identity=number, count=2, parentGroup=None, isCollapsed=not number,
                        index=3 if not number else -1, item=lambda i, n=nodes: n[i])
            for node in nodes:
                node.parentGroup = parent
                node.index = -1 if not number else node.index - 1
        self.design.timeline.count = self.design.timeline.markerPosition = 6
        result = self.chain.plan(self.design, self.records[0], self.choices)
        self.assertEqual([(item[0], item[1]) for item in result], [(3, 3), (4, 5)])

    def test_last_batch_retains_existing_single_batch_edit_path(self):
        with patch.object(self.edit, 'update', return_value=['last preview']) as update:
            result = self.chain.update(self.design, self.records[1], self.values,
                                      persist=False, batch_choices=self.choices)
        update.assert_called_once_with(self.design, self.records[1], self.values, persist=False)
        self.assertEqual(result, ['last preview'])
