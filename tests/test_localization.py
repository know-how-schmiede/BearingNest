"""Locale coverage, format safety and persisted-mode compatibility."""
import importlib
from pathlib import Path
from string import Formatter
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / 'Fusion-Add-In' / 'BearingNest'
PACKAGE = '_bearingnest_locale_tests'
package = ModuleType(PACKAGE)
package.__path__ = [str(ROOT)]
sys.modules[PACKAGE] = package
strings = importlib.import_module(PACKAGE + '.strings')
german = importlib.import_module(PACKAGE + '.strings_de')


class LocalizationTests(unittest.TestCase):
    def tearDown(self):
        strings.set_locale('en')

    def test_complete_german_keys_and_format_specifications(self):
        self.assertEqual(set(strings.ENGLISH_TEXT), set(german.TEXT))
        def tokens(text):
            return sorted((name, spec, conversion) for _, name, spec, conversion
                          in Formatter().parse(text) if name is not None)
        for key, source in strings.ENGLISH_TEXT.items():
            with self.subTest(key=key):
                self.assertEqual(tokens(source), tokens(german.TEXT[key]))

    def test_fields_translate_in_place_and_restore_without_changing_units(self):
        fields = strings.PARAMETER_FIELDS
        original = list(fields)
        strings.set_locale('de-DE')
        self.assertIs(fields, strings.PARAMETER_FIELDS)
        for source, translated in zip(original, fields):
            self.assertNotEqual(source[1], translated[1])
            self.assertEqual(source[0], translated[0])
            self.assertEqual(source[2:], translated[2:])
        for source_fields in strings._FIELD_SOURCES:
            for row in source_fields:
                self.assertIn(row[1], german.LABELS)
        strings.set_locale('fr')
        self.assertEqual(fields, original)

    def test_modes_round_trip_without_translating_storage(self):
        strings.set_locale('de')
        for mode in ('Off', 'Through All', 'Blind'):
            self.assertNotEqual(strings.label(mode), mode)
            self.assertEqual(strings.source_label(strings.label(mode)), mode)
            self.assertEqual(strings.source_label(mode), mode)

    def test_fusion_preference_and_missing_preference_fallback(self):
        core = ModuleType('adsk.core')
        core.UserLanguages = SimpleNamespace(GermanLanguage=5)
        adsk = ModuleType('adsk')
        adsk.core = core
        with patch.dict(sys.modules, {'adsk': adsk, 'adsk.core': core}):
            app = SimpleNamespace(preferences=SimpleNamespace(
                generalPreferences=SimpleNamespace(userLanguage=5)))
            strings.configure_from_fusion(app)
            self.assertEqual(strings.TEXT['bearing_seat'], 'Lagersitz')
            strings.configure_from_fusion(SimpleNamespace())
            self.assertEqual(strings.TEXT['bearing_seat'], 'Bearing Seat')
