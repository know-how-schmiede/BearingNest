"""Copy version.py's version into Fusion's JSON manifest and README header."""
import argparse
import json
from pathlib import Path
import re
import runpy

ROOT = Path(__file__).resolve().parents[1]


def synchronize(root=ROOT, *, check=False):
    root = Path(root)
    addin = root / 'Fusion-Add-In' / 'BearingNest'
    version = runpy.run_path(str(addin / 'version.py'))['VERSION']
    if not isinstance(version, str) or not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('VERSION must use major.minor.patch format.')
    manifest_path = addin / 'BearingNest.manifest'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    readme_path = root / 'README.md'
    readme = readme_path.read_text(encoding='utf-8-sig')
    updated_readme, count = re.subn(
        r'(?m)^Version: \*\*[^*\r\n]+\*\*',
        f'Version: **{version}**', readme)
    if count != 1:
        raise ValueError('Expected exactly one current-version header in README.md.')
    changed = []
    if manifest.get('version') != version:
        changed.append(manifest_path)
    if readme != updated_readme:
        changed.append(readme_path)
    if not check:
        if manifest_path in changed:
            manifest['version'] = version
            manifest_path.write_text(json.dumps(manifest, indent=4, ensure_ascii=False) + '\n',
                                     encoding='utf-8')
        if readme_path in changed:
            readme_path.write_text(updated_readme, encoding='utf-8')
    return changed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Report drift without writing files.')
    args = parser.parse_args()
    changes = synchronize(check=args.check)
    for path in changes:
        print(f'{"Out of sync" if args.check else "Updated"}: {path.relative_to(ROOT)}')
    if not changes:
        print('Manifest and README match version.py.')
    raise SystemExit(1 if args.check and changes else 0)
