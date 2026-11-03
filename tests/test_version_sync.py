"""Check version propagation and read-only drift detection."""
import json
from pathlib import Path
import runpy
import tempfile
import unittest

SYNC = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'tools/sync_version.py'))


class VersionSyncTests(unittest.TestCase):
    def test_sync_updates_current_version_and_preserves_history_and_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            addin = root / 'Fusion-Add-In/BearingNest'
            addin.mkdir(parents=True)
            (addin / 'version.py').write_text("VERSION = '0.2.1'\n", encoding='utf-8')
            manifest = addin / 'BearingNest.manifest'
            manifest.write_text('{"version": "0.1.0", "author": "Owner"}', encoding='utf-8')
            readme = root / 'README.md'
            readme.write_text('Version: **0.1.0** · Status: test\n\nHistory: 0.1.0\n',
                              encoding='utf-8')
            before = (manifest.read_bytes(), readme.read_bytes())
            self.assertEqual(len(SYNC['synchronize'](root, check=True)), 2)
            self.assertEqual((manifest.read_bytes(), readme.read_bytes()), before)
            self.assertEqual(len(SYNC['synchronize'](root)), 2)
            self.assertEqual(json.loads(manifest.read_text()),
                             {'version': '0.2.1', 'author': 'Owner'})
            self.assertIn('Version: **0.2.1**', readme.read_text(encoding='utf-8'))
            self.assertIn('History: 0.1.0', readme.read_text(encoding='utf-8'))
            self.assertEqual(SYNC['synchronize'](root, check=True), [])

    def test_repository_versions_are_synchronized(self):
        self.assertEqual(SYNC['synchronize'](check=True), [])


if __name__ == '__main__':
    unittest.main()
