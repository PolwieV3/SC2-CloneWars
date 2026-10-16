"""Verify the current development copy and staged mod against its snapshot."""
import json
import pathlib
import zipfile

from snapshot import ROOT, digest
from build import NAME


def main():
    manifest = json.loads((ROOT / 'inventory/snapshot-manifest.json').read_text())
    snapshot = ROOT / 'local/installed-snapshot'
    dev = ROOT / 'local/dev-game'
    differences = []
    missing = []
    snapshot_failures = []
    for row in manifest['files']:
        original = snapshot / row['path']
        if not original.is_file() or digest(original) != row['sha256']:
            snapshot_failures.append(row['path'])
        p = dev / row['path']
        if not row['in_dev_copy']:
            if p.exists():
                differences.append(row['path'])
            continue
        if not p.is_file():
            missing.append(row['path'])
        elif digest(p) != row['sha256']:
            differences.append(row['path'])
    raw = (snapshot / 'bin/GameDataPath.lua').read_bytes()
    lines = raw.splitlines(keepends=True)
    expected_loader = b''.join(line for line in lines if not line.startswith(b"mount_contents(SHGetFolderPath('PERSONAL')"))
    loader_matches = (dev / 'bin/GameDataPath.lua').read_bytes() == expected_loader
    added = sorted(p.relative_to(dev).as_posix() for p in dev.rglob('*') if p.is_file()
                   and p.relative_to(dev).as_posix() not in {r['path'] for r in manifest['files'] if r['in_dev_copy']})
    packages = [NAME]
    for candidate in ['zz_SC2_CloneWars_TX130_Model.scd','zz_SC2_CloneWars_TX130_Audio.scd','zz_SC2_CloneWars_TX130_Blaster.scd']:
        if (dev / 'gamedata' / candidate).exists():
            packages.append(candidate)
    staged_matches = all((dev / 'gamedata' / name).read_bytes() == (ROOT / 'dist' / name).read_bytes() for name in packages)
    archive_failures = []
    for p in sorted((dev / 'gamedata').glob('*.scd')):
        with zipfile.ZipFile(p) as z:
            failed = z.testzip()
            if failed:
                archive_failures.append({'archive': p.name, 'entry': failed})
    passed = (not missing and not snapshot_failures and differences == ['bin/GameDataPath.lua']
              and loader_matches and added == sorted('gamedata/' + name for name in packages) and staged_matches and not archive_failures)
    report = {'baseline': manifest['baseline'], 'checked_files': len(manifest['files']),
              'snapshot_failures': snapshot_failures, 'missing_files': missing,
              'only_changed_copied_files': differences, 'isolated_loader_matches': loader_matches,
              'added_files': added, 'staged_mod_matches_build': staged_matches,
              'archive_crc_failures': archive_failures, 'passed': passed}
    (ROOT / 'inventory/dev-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
