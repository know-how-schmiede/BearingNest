"""Transient preview replay/appearance ownership without native Fusion rendering."""
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1] / 'Fusion-Add-In/BearingNest'


class CachedPreviewTests(unittest.TestCase):
    def setUp(self):
        package = ModuleType('cached_graphics_test')
        package.__path__ = [str(ROOT)]
        adsk, fusion = ModuleType('adsk'), ModuleType('adsk.fusion')
        adsk.fusion = fusion
        self.manager = NS(copy=Mock(return_value=object()))
        fusion.TemporaryBRepManager = NS(get=lambda: self.manager)
        fusion.CustomGraphicsAppearanceColorEffect = NS(create=lambda appearance: appearance)
        self.modules = patch.dict(sys.modules, {'cached_graphics_test': package,
            'adsk': adsk, 'adsk.fusion': fusion})
        self.modules.start()
        self.model = importlib.import_module('cached_graphics_test.cached_preview')
        self.source = NS(isValid=True, isVisible=True, opacity=0.6,
                         visibleOpacity=0.6, appearance=object(), isLightBulbOn=True)
        self.graphics = NS(setOpacity=Mock(return_value=True))
        self.group = NS(isValid=True, deleteMe=Mock(return_value=True),
                        addBRepBody=Mock(return_value=self.graphics))
        self.design = NS(rootComponent=NS(customGraphicsGroups=NS(add=Mock(return_value=self.group))))
        self.feedback = dict(placements={1: (object(), object())}, issues={}, warnings={1: ['Thin wall']})

    def tearDown(self):
        self.modules.stop()

    def test_capture_is_detached_and_replay_restores_source_appearance(self):
        cache = self.model.CachedPreview(self.source, self.feedback)
        self.assertEqual(self.source.opacity, 0.6)
        self.feedback['warnings'][1].append('Later message')
        self.assertEqual(cache.feedback['warnings'][1], ['Thin wall'])
        cache.show(self.design, self.source)
        self.group.addBRepBody.assert_called_once_with(cache.body)
        self.assertEqual(self.source.opacity, 0)
        self.assertTrue(self.source.isLightBulbOn)
        self.assertFalse(self.graphics.isSelectable)
        self.graphics.setOpacity.assert_called_once_with(0.6, True)
        cache.clear()
        self.assertEqual(self.source.opacity, 0.6)
        self.assertIsNone(cache.source)
        self.assertIsNone(cache.group)

    def test_failed_display_restores_source_and_discards_graphics(self):
        cache = self.model.CachedPreview(self.source, self.feedback)
        self.group.addBRepBody.return_value = None
        with self.assertRaises(RuntimeError):
            cache.show(self.design, self.source)
        self.assertEqual(self.source.opacity, 0.6)
        self.group.deleteMe.assert_called_once()
        self.assertIsNone(cache.group)

    def test_failed_graphics_cleanup_restores_source_and_retains_retry(self):
        cache = self.model.CachedPreview(self.source, self.feedback)
        cache.show(self.design, self.source)
        self.group.deleteMe.return_value = False
        with self.assertRaises(RuntimeError):
            cache.clear()
        self.assertEqual(self.source.opacity, 0.6)
        self.assertIs(cache.group, self.group)
        self.group.deleteMe.return_value = True
        cache.clear()
        self.assertIsNone(cache.group)

    def test_unavailable_copy_and_invisible_source_use_caller_fallback(self):
        self.manager.copy.return_value = None
        with self.assertRaises(RuntimeError):
            self.model.CachedPreview(self.source, self.feedback)
        self.manager.copy.return_value = object()
        cache = self.model.CachedPreview(self.source, self.feedback)
        self.source.isVisible = False
        with self.assertRaises(RuntimeError):
            cache.show(self.design, self.source)
        self.design.rootComponent.customGraphicsGroups.add.assert_not_called()
