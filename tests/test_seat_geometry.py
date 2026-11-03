"""Transaction adapter checks with an API substitute, not a Fusion kernel test."""
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1] / 'Fusion-Add-In/BearingNest'


class Vector:
    def __init__(self, x=0, y=0, z=1):
        self.x, self.y, self.z = x, y, z

    def normalize(self):
        return True

    def dotProduct(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def copy(self):
        return Vector(self.x, self.y, self.z)

    def scaleBy(self, value):
        self.x *= value
        self.y *= value
        self.z *= value


class Point:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

    def vectorTo(self, other):
        return Vector(other.x - self.x, other.y - self.y, other.z - self.z)

    def distanceTo(self, other):
        return ((self.x-other.x)**2 + (self.y-other.y)**2 + (self.z-other.z)**2)**0.5


class ComputedProfiles:
    """Regression substitute: suppressed/deferred profiles cannot be extruded."""
    def __init__(self, sketch):
        self.sketch = sketch

    @property
    def count(self):
        return int(self.sketch.areProfilesShown and not self.sketch.isComputeDeferred)

    def item(self, index):
        if self.count != 1 or index != 0:
            raise RuntimeError('No computed profile is available')
        return 'profile'


class GeometryAdapterTests(unittest.TestCase):
    def setUp(self):
        package = ModuleType('geometry_test')
        package.__path__ = [str(ROOT)]
        core, fusion, adsk = ModuleType('adsk.core'), ModuleType('adsk.fusion'), ModuleType('adsk')
        adsk.core, adsk.fusion = core, fusion
        core.Point3D = NS(create=Point)
        core.ValueInput = NS(createByString=lambda value: value)
        core.ObjectCollection = NS(create=lambda: NS(add=lambda value: None))
        core.Matrix3D = NS(create=lambda: NS())
        fusion.ExtentDirections = NS(NegativeExtentDirection=-1, PositiveExtentDirection=1)
        fusion.FeatureOperations = NS(NewBodyFeatureOperation='new', CutFeatureOperation='cut')
        fusion.BooleanTypes = NS(IntersectionBooleanType='intersection', DifferenceBooleanType='difference')
        fusion.SketchPoint = type('SketchPoint', (), {})
        self.sketch_point_type = fusion.SketchPoint
        fusion.DistanceExtentDefinition = NS(create=lambda value: value)
        fusion.OffsetStartDefinition = NS(create=lambda value: NS(offset=value))
        fusion.ThroughAllExtentDefinition = NS(create=lambda: NS(isPositiveDirection=True))
        fusion.FeatureHealthStates = NS(HealthyFeatureHealthState=0)
        self.manager = NS(copy=Mock(return_value=NS(volume=2)))
        fusion.TemporaryBRepManager = NS(get=lambda: self.manager)
        self.modules = patch.dict(sys.modules, {'geometry_test': package,
            'adsk': adsk, 'adsk.core': core, 'adsk.fusion': fusion})
        self.modules.start()
        self.geometry = importlib.import_module('geometry_test.seat_geometry')
        self.parameters = importlib.import_module('geometry_test.seat_parameters').SeatParameters()
        self.deleted = []

        def entity(name, **kwargs):
            result = NS(isValid=True, entityToken=name, healthState=0, errorOrWarningMessage='', **kwargs)
            def delete():
                result.isValid = False
                self.deleted.append(name)
                return True
            result.deleteMe = delete
            return result
        self.entity = entity

        self.sketch = entity('sketch', profiles=NS(count=1, item=lambda index: 'profile'),
            modelToSketchSpace=lambda point: Point(0, 0, 0), sketchToModelSpace=lambda point: point,
            sketchCurves=NS(sketchLines=NS(addByTwoPoints=Mock(return_value=NS())),
                            sketchArcs=NS(addByThreePoints=Mock(return_value=NS()))))
        self.sketch.areProfilesShown = True
        self.sketch.isComputeDeferred = False
        self.sketch.profiles = ComputedProfiles(self.sketch)
        self.tool_body = NS(volume=2)
        self.tool = entity('tool', bodies=NS(count=1, item=lambda index: self.tool_body))
        self.result_body = NS(entityToken='result_body', volume=9)
        self.cut = entity('cut', bodies=NS(count=1, item=lambda index: self.result_body))
        self.tool_input = NS(setOneSideExtent=Mock(return_value=True))
        self.cut_input = NS(setOneSideExtent=Mock(return_value=True))
        self.extrudes = NS(createInput=Mock(side_effect=[self.tool_input, self.cut_input]),
                           add=Mock(side_effect=[self.tool, self.cut]))
        self.design = NS(rootComponent=NS(sketches=NS(addWithoutEdges=Mock(return_value=self.sketch)),
            features=NS(extrudeFeatures=self.extrudes)))
        self.face = NS(body=NS(entityToken='body', volume=10), entityToken='face')
        self.position = NS(entityToken='point')
        self.placement = patch.object(self.geometry, 'placement', return_value=(Point(0, 0, 0), Vector()))
        self.placement.start()

    def tearDown(self):
        self.placement.stop()
        self.modules.stop()

    def build(self, persist):
        return self.geometry.create_seat(self.design, self.face, self.position,
                                         self.parameters, persist=persist)

    def test_preview_builds_inward_cut_without_writing_metadata(self):
        with patch.object(self.geometry, '_fully_contained'), \
                patch.object(self.geometry.seat_storage, 'save') as save:
            self.assertIs(self.build(False), self.cut)
        save.assert_not_called()
        self.tool_input.setOneSideExtent.assert_called_once_with('7 mm', -1)
        self.cut_input.setOneSideExtent.assert_called_once_with('7 mm', -1)
        self.assertEqual(self.extrudes.createInput.call_args.args, ('profile', 'cut'))
        self.assertEqual(self.cut_input.participantBodies, [self.face.body])
        self.assertEqual(self.deleted, ['tool'])
        self.assertTrue(self.sketch.areProfilesShown)
        self.assertFalse(self.sketch.isVisible)

    def test_commit_saves_manual_bearing_and_effective_values_on_cut_feature(self):
        with patch.object(self.geometry, '_fully_contained'), \
                patch.object(self.geometry.seat_storage, 'save') as save:
            self.build(True)
        owner, snapshot = save.call_args.args
        self.assertIs(owner, self.cut)
        self.assertEqual(snapshot['features']['seat_cut'], 'cut')
        self.assertEqual(snapshot['references']['position'], 'point')
        self.assertAlmostEqual(snapshot['parameters']['contact_mm'], 21.9)
        self.assertIsNone(snapshot['bearing']['d_mm'])
        self.assertNotIn('tool', snapshot['features'])

    def test_breakout_rejects_before_cut_and_removes_tool_and_sketch(self):
        with patch.object(self.geometry, '_fully_contained', side_effect=ValueError('breakout')):
            with self.assertRaisesRegex(ValueError, 'breakout'):
                self.build(True)
        self.assertEqual(self.extrudes.add.call_count, 1)
        self.assertEqual(self.deleted, ['tool', 'sketch'])

    def test_metadata_failure_removes_every_created_feature_in_reverse_order(self):
        with patch.object(self.geometry, '_fully_contained'), \
                patch.object(self.geometry.seat_storage, 'save', side_effect=RuntimeError('storage')):
            with self.assertRaisesRegex(RuntimeError, 'storage'):
                self.build(True)
        self.assertEqual(self.deleted, ['tool', 'cut', 'sketch'])

    def test_containment_uses_entire_tool_and_checks_a_remaining_floor(self):
        copies = [NS(volume=2), NS(volume=1.99)]
        manager = NS(copy=Mock(side_effect=copies), transform=Mock(return_value=True),
                     booleanOperation=Mock(return_value=True))
        with self.assertRaisesRegex(ValueError, 'breaks out'):
            self.geometry._fully_contained(manager, self.tool_body, self.face.body, Vector(z=-1))
        self.assertEqual(manager.booleanOperation.call_count, 2)
        manager.transform.assert_called_once()

    def test_kernel_failure_cannot_be_treated_as_valid_containment(self):
        manager = NS(copy=Mock(return_value=NS(volume=2)), booleanOperation=Mock(return_value=False))
        with self.assertRaises(ValueError):
            self.geometry._fully_contained(manager, self.tool_body, self.face.body, Vector(z=-1))

    def test_reversed_face_normal_uses_positive_sketch_extent(self):
        self.geometry.placement.return_value = (Point(0, 0, 0), Vector(z=-1))
        with patch.object(self.geometry, '_fully_contained'):
            self.build(False)
        self.tool_input.setOneSideExtent.assert_called_once_with('7 mm', 1)

    def test_full_containment_passes_both_floor_and_tool_checks(self):
        manager = NS(copy=Mock(side_effect=[NS(volume=2), NS(volume=2)]),
                     transform=Mock(return_value=True), booleanOperation=Mock(return_value=True))
        self.geometry._fully_contained(manager, self.tool_body, self.face.body, Vector(z=-1))
        self.assertEqual(manager.booleanOperation.call_count, 2)

    def configure_batch(self, count=2):
        sketches, tools, cuts, inputs = [], [], [], []
        source = NS(areProfilesShown=True, isVisible=True, isValid=True)
        positions = []
        for index in range(count):
            sketches.append(self.entity(f'sketch{index}',
                profiles=NS(count=1, item=lambda offset: 'profile'),
                modelToSketchSpace=lambda point: point, sketchToModelSpace=lambda point: point,
                sketchCurves=self.sketch.sketchCurves))
            sketches[-1].areProfilesShown = True
            sketches[-1].isComputeDeferred = False
            sketches[-1].profiles = ComputedProfiles(sketches[-1])
            tools.append(self.entity(f'tool{index}', bodies=NS(count=1, item=lambda offset: self.tool_body)))
            result = NS(entityToken=f'result{index}', volume=9-index)
            cuts.append(self.entity(f'cut{index}', bodies=NS(count=1, item=lambda offset, result=result: result)))
            position = self.sketch_point_type()
            position.parentSketch = source
            position.entityToken = f'position{index}'
            positions.append(position)
        for index in range(count * 2):
            inputs.append(NS(setOneSideExtent=Mock(return_value=True)))
        self.design.rootComponent.sketches.addWithoutEdges.side_effect = sketches
        self.extrudes.createInput.side_effect = inputs
        self.batch_inputs = inputs
        self.result_body = cuts[0].bodies.item(0)
        self.extrudes.add.side_effect = [*tools, *cuts]
        self.geometry.placement.side_effect = [(Point(index * 10, 0, 0), Vector()) for index in range(count)]
        return positions, source, sketches, tools, cuts

    def test_batch_checks_every_position_and_pair_before_first_cut(self):
        positions, source, sketches, tools, cuts = self.configure_batch(3)
        with patch.object(self.geometry, '_fully_contained') as contained, \
                patch.object(self.geometry, '_check_overlap') as overlap, \
                patch.object(self.geometry.seat_storage, 'save') as save:
            pending = iter([*tools, *cuts])
            def add(feature_input):
                feature = next(pending)
                if feature in cuts:
                    self.assertEqual(contained.call_count, 3)
                    self.assertEqual(overlap.call_count, 3)
                    self.assertTrue(all(not tool.isValid for tool in tools))
                return feature
            self.extrudes.add.side_effect = add
            result = self.geometry.create_seats(self.design, self.face, positions, self.parameters, persist=True)
        self.assertEqual(result, cuts)
        self.assertEqual(save.call_count, 3)
        identities = [call.args[1]['seat_id'] for call in save.call_args_list]
        self.assertEqual(len(set(identities)), 3)
        self.assertFalse(source.areProfilesShown)
        self.assertTrue(source.isVisible)
        self.assertTrue(all(not sketch.isVisible and sketch.areProfilesShown for sketch in sketches))

    def test_profile_calculation_stays_enabled_for_hidden_validation_and_cut_sketch(self):
        # The old constant-count substitute missed this 0.1.3/0.1.4 regression.
        self.sketch.areProfilesShown = False
        with patch.object(self.geometry, '_fully_contained'):
            self.build(False)
        self.assertEqual(self.sketch.profiles.count, 1)
        self.assertFalse(self.sketch.isVisible)
        self.assertTrue(self.sketch.areProfilesShown)
        self.assertEqual(self.extrudes.createInput.call_count, 2)

    def test_invalid_second_position_leaves_no_partial_batch(self):
        positions, source, sketches, tools, cuts = self.configure_batch()
        with patch.object(self.geometry, '_fully_contained', side_effect=[None, ValueError('breakout')]), \
                patch.object(self.geometry, '_check_overlap'), \
                patch.object(self.geometry.seat_storage, 'save') as save:
            with self.assertRaisesRegex(ValueError, 'Position 2.*breakout'):
                self.geometry.create_seats(self.design, self.face, positions, self.parameters, persist=True)
        self.assertEqual(self.extrudes.add.call_count, 2)
        self.assertEqual(self.deleted, ['tool1', 'sketch1', 'tool0', 'sketch0'])
        save.assert_not_called()
        self.assertTrue(source.areProfilesShown)

    def test_overlapping_positions_are_rejected_before_any_direct_cut(self):
        positions, source, sketches, tools, cuts = self.configure_batch()
        with patch.object(self.geometry, '_fully_contained'), \
                patch.object(self.geometry, '_check_overlap', side_effect=ValueError('overlap')):
            with self.assertRaisesRegex(ValueError, 'Positions 1 and 2.*overlap'):
                self.geometry.create_seats(self.design, self.face, positions, self.parameters, persist=True)
        self.assertEqual(self.extrudes.add.call_count, 2)
        self.assertFalse(any(name.startswith('cut') for name in self.deleted))
        self.assertTrue(all(not sketch.isValid for sketch in sketches))

    def test_later_cut_failure_removes_prior_cut_and_restores_profile_fills(self):
        positions, source, sketches, tools, cuts = self.configure_batch()
        self.extrudes.add.side_effect = [*tools, cuts[0], RuntimeError('second cut failed')]
        with patch.object(self.geometry, '_fully_contained'), \
                patch.object(self.geometry, '_check_overlap'), \
                patch.object(self.geometry.seat_storage, 'save') as save:
            with self.assertRaisesRegex(RuntimeError, 'second cut failed'):
                self.geometry.create_seats(self.design, self.face, positions, self.parameters, persist=True)
        save.assert_not_called()
        self.assertFalse(cuts[0].isValid)
        self.assertTrue(all(not sketch.isValid for sketch in sketches))
        self.assertTrue(source.areProfilesShown)

    def test_duplicate_centers_are_rejected_before_feature_creation(self):
        positions, source, sketches, tools, cuts = self.configure_batch()
        self.geometry.placement.side_effect = [(Point(0, 0, 0), Vector()), (Point(0, 0, 0), Vector())]
        with self.assertRaisesRegex(ValueError, 'same center'):
            self.geometry.create_seats(self.design, self.face, positions, self.parameters, persist=True)
        self.design.rootComponent.sketches.addWithoutEdges.assert_not_called()

    def test_batch_preview_does_not_change_source_sketch_profile_preferences(self):
        positions, source, sketches, tools, cuts = self.configure_batch()
        with patch.object(self.geometry, '_fully_contained'), \
                patch.object(self.geometry, '_check_overlap'), \
                patch.object(self.geometry.seat_storage, 'save') as save:
            self.geometry.create_seats(self.design, self.face, positions, self.parameters, persist=False)
        self.assertTrue(source.areProfilesShown)
        self.assertTrue(source.isVisible)
        save.assert_not_called()

    def test_failure_saving_second_snapshot_removes_all_cuts_and_restores_source_display(self):
        positions, source, sketches, tools, cuts = self.configure_batch()
        with patch.object(self.geometry, '_fully_contained'), \
                patch.object(self.geometry, '_check_overlap'), \
                patch.object(self.geometry.seat_storage, 'save', side_effect=[None, RuntimeError('second snapshot')]):
            with self.assertRaisesRegex(RuntimeError, 'second snapshot'):
                self.geometry.create_seats(self.design, self.face, positions, self.parameters, persist=True)
        self.assertTrue(all(not cut.isValid for cut in cuts))
        self.assertTrue(source.areProfilesShown)
        self.assertTrue(source.isVisible)

    def test_exact_overlap_check_detects_removed_volume_and_fails_closed_on_kernel_error(self):
        envelope = NS(boundingBox=NS(minPoint=Point(0, 0, 0), maxPoint=Point(1, 1, 1)))
        for remaining_volume, success, expected_error in ((2, True, False), (1.9, True, True), (2, False, True)):
            remaining = NS(volume=2)
            def difference(target, tool, operation):
                target.volume = remaining_volume
                return success
            manager = NS(copy=Mock(return_value=remaining), booleanOperation=difference)
            if expected_error:
                with self.assertRaises(ValueError):
                    self.geometry._check_overlap(manager, envelope, envelope)
            else:
                self.geometry._check_overlap(manager, envelope, envelope)

    def test_disjoint_bounding_boxes_skip_unnecessary_kernel_operations(self):
        first = NS(boundingBox=NS(minPoint=Point(0, 0, 0), maxPoint=Point(1, 1, 1)))
        second = NS(boundingBox=NS(minPoint=Point(2, 0, 0), maxPoint=Point(3, 1, 1)))
        manager = NS(copy=Mock(), booleanOperation=Mock())
        self.geometry._check_overlap(manager, first, second)
        manager.copy.assert_not_called()
        manager.booleanOperation.assert_not_called()

    def configure_clearance(self, mode='Blind'):
        positions, source, sketches, tools, cuts = self.configure_batch(3)
        self.geometry.placement.side_effect = [(Point(0, 0, 0), Vector())]
        self.sketch.sketchCurves.sketchCircles = NS(addByCenterRadius=Mock(return_value=NS()))
        self.face.body.boundingBox = NS(minPoint=Point(-3, -3, -2), maxPoint=Point(3, 3, 0))
        self.parameters = self.parameters.__class__(shaft_mode=mode, inner_relief_enabled=True,
            inner_diameter_mm=12, inner_depth_mm=0.4, axial_mm=0.5)
        return positions[:1], source, sketches, tools, cuts

    def test_blind_and_inner_relief_preflight_then_commit_correct_offsets_and_snapshot(self):
        positions, source, sketches, tools, cuts = self.configure_clearance()
        with patch.object(self.geometry, '_fully_contained') as contained, \
                patch.object(self.geometry.seat_storage, 'save') as save:
            result = self.geometry.create_seats(self.design, self.face, positions, self.parameters, persist=True)
        self.assertEqual(contained.call_count, 3)
        self.assertEqual(result, [cuts[0]])
        self.assertTrue(all(not tool.isValid for tool in tools))
        self.batch_inputs[1].setOneSideExtent.assert_called_once_with('12 mm', -1)
        self.assertEqual(self.batch_inputs[2].startExtent.offset, '-7.5 mm')
        self.assertEqual(self.batch_inputs[5].startExtent.offset, '-7.5 mm')
        self.batch_inputs[5].setOneSideExtent.assert_called_once_with('0.4 mm', -1)
        snapshot = save.call_args.args[1]
        self.assertEqual(snapshot['bearing']['d_mm'], 8)
        self.assertIsNone(snapshot['bearing']['inner_ring_outside_mm'])
        self.assertEqual(snapshot['features']['shaft_cut'], 'cut1')
        self.assertEqual(snapshot['features']['inner_ring_relief'], 'cut2')
        self.assertAlmostEqual(self.sketch.sketchCurves.sketchCircles.addByCenterRadius.call_args_list[0].args[1], 0.41)
        self.assertTrue(all(not sketch.isVisible and sketch.areProfilesShown for sketch in sketches))

    def test_through_all_has_finite_preflight_but_native_through_all_final_cut(self):
        positions, source, sketches, tools, cuts = self.configure_clearance('Through All')
        with patch.object(self.geometry, '_fully_contained') as contained:
            self.geometry.create_seats(self.design, self.face, positions, self.parameters, persist=False)
        self.assertEqual(contained.call_count, 2)  # Shaft exit is intentional; seat and relief stay contained.
        self.batch_inputs[1].setOneSideExtent.assert_called_once_with('21 mm', -1)
        extent, direction = self.batch_inputs[4].setOneSideExtent.call_args.args
        self.assertFalse(extent.isPositiveDirection)
        self.assertEqual(direction, -1)
        self.assertEqual(self.batch_inputs[4].participantBodies, [self.result_body])

    def test_inner_relief_breakout_rejects_every_operation_before_first_cut(self):
        positions, source, sketches, tools, cuts = self.configure_clearance()
        with patch.object(self.geometry, '_fully_contained', side_effect=[None, None, ValueError('relief breakout')]), \
                patch.object(self.geometry.seat_storage, 'save') as save:
            with self.assertRaisesRegex(ValueError, 'relief breakout'):
                self.geometry.create_seats(self.design, self.face, positions, self.parameters, persist=True)
        self.assertEqual(self.extrudes.add.call_count, 3)
        self.assertTrue(all(not tool.isValid and not sketch.isValid for tool, sketch in zip(tools, sketches)))
        save.assert_not_called()

    def test_failed_shaft_cut_removes_seat_cut_and_all_clearance_sketches(self):
        positions, source, sketches, tools, cuts = self.configure_clearance()
        self.extrudes.add.side_effect = [*tools, cuts[0], RuntimeError('shaft cut failed')]
        with patch.object(self.geometry, '_fully_contained'), \
                patch.object(self.geometry.seat_storage, 'save') as save:
            with self.assertRaisesRegex(RuntimeError, 'shaft cut failed'):
                self.geometry.create_seats(self.design, self.face, positions, self.parameters, persist=True)
        self.assertFalse(cuts[0].isValid)
        self.assertTrue(all(not sketch.isValid for sketch in sketches))
        self.assertTrue(source.areProfilesShown)
        save.assert_not_called()

    def test_positive_direction_uses_positive_inner_relief_start_offset(self):
        with patch.object(self.geometry.adsk.fusion.OffsetStartDefinition, 'create', wraps=lambda value: NS(offset=value)):
            self.geometry._extrude(self.design, self.sketch, self.parameters, 1, 'new',
                                   depth_mm=0.4, start_mm=7.5)
        self.assertEqual(self.tool_input.startExtent.offset, '7.5 mm')

    def test_native_through_all_explicitly_sets_its_own_positive_direction(self):
        self.geometry._extrude(self.design, self.sketch, self.parameters, 1, 'new', through_all=True)
        extent, direction = self.tool_input.setOneSideExtent.call_args.args
        self.assertTrue(extent.isPositiveDirection)
        self.assertEqual(direction, 1)

    def test_healthy_but_ineffective_cut_is_deleted_and_rejected(self):
        self.result_body.volume = self.face.body.volume
        self.extrudes.add.side_effect = [self.cut]
        with self.assertRaisesRegex(ValueError, 'removed no material'):
            self.geometry._extrude(self.design, self.sketch, self.parameters, -1, 'cut', self.face.body)
        self.assertFalse(self.cut.isValid)
        self.assertEqual(self.deleted, ['cut'])

    def test_warning_feature_is_deleted_before_it_can_be_reported_as_valid(self):
        self.cut.healthState = 1
        self.cut.errorOrWarningMessage = 'No target material was cut'
        self.extrudes.add.side_effect = [self.cut]
        with self.assertRaisesRegex(RuntimeError, 'No target material'):
            self.geometry._extrude(self.design, self.sketch, self.parameters, -1, 'cut', self.face.body)
        self.assertFalse(self.cut.isValid)

    def test_shaft_warning_removes_prior_seat_cut_and_restores_source_display(self):
        positions, source, sketches, tools, cuts = self.configure_clearance('Through All')
        cuts[1].healthState = 1
        cuts[1].errorOrWarningMessage = 'Shaft direction misses body'
        with patch.object(self.geometry, '_fully_contained'), \
                patch.object(self.geometry.seat_storage, 'save') as save:
            with self.assertRaisesRegex(RuntimeError, 'Shaft direction misses body'):
                self.geometry.create_seats(self.design, self.face, positions, self.parameters, persist=True)
        self.assertFalse(cuts[0].isValid)
        self.assertFalse(cuts[1].isValid)
        self.assertTrue(source.areProfilesShown)
        save.assert_not_called()
