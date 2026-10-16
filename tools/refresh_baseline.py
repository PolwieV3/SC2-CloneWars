"""Rescan every installed file and replace local copies, retaining old baseline history."""
import argparse
import csv
from datetime import datetime, timezone
import json
import pathlib
import re
import shutil

from snapshot import ROOT, EXTRAS, digest


def local_path(path):
    resolved = path.resolve()
    if not resolved.is_relative_to((ROOT / 'local').resolve()):
        raise RuntimeError(f'Local operation escaped workspace: {resolved}')
    return resolved


def steam_evidence(source, log):
    manifest = source.parents[1] / 'appmanifest_40100.acf'
    text = manifest.read_text(encoding='utf-8')
    build = re.search(r'"buildid"\s+"(\d+)"', text)
    lines = log.read_text(encoding='utf-8', errors='replace').splitlines()
    starts = [i for i, line in enumerate(lines) if 'Start validating appID 40100' in line]
    if not starts:
        raise RuntimeError('No SC2 validation start found in Steam log.')
    relevant = []
    for line in lines[starts[-1]:]:
        if '40100' not in line:
            continue
        relevant.append(line)
        if 'scheduler finished' in line:
            break
    if not relevant or 'scheduler finished' not in relevant[-1] or 'result No Error' not in relevant[-1]:
        raise RuntimeError('Latest Steam validation has not completed successfully.')
    return {'build_id': build.group(1) if build else None,
            'dlc_depot_40135_installed': '"40135"' in text,
            'steam_validation': relevant,
            'scope': 'Steam verification plus full local file hash scan; no independent depot-manifest comparison'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('installation', type=pathlib.Path)
    ap.add_argument('--steam-log', type=pathlib.Path, required=True)
    args = ap.parse_args()
    source = args.installation.resolve()
    if source.is_relative_to(ROOT.resolve()):
        raise RuntimeError('Use the real installation, not a project copy.')
    if not (source / 'bin/SupremeCommander2.exe').is_file():
        raise RuntimeError('SC2 executable not found.')
    evidence = steam_evidence(source, args.steam_log)
    known_extras = sorted(p.relative_to(source).as_posix() for p in (source / 'gamedata').rglob('*')
                          if p.name.lower() in EXTRAS)
    if known_extras:
        raise RuntimeError(f'Known third-party leftovers remain: {known_extras}')
    files = sorted(p for p in source.rglob('*') if p.is_file())
    for p in files:
        if not p.resolve().is_relative_to(source):
            raise RuntimeError(f'File link points outside installation: {p}')
    size = sum(p.stat().st_size for p in files)
    if shutil.disk_usage(ROOT).free < size * 2 + 1024**3:
        raise RuntimeError('Insufficient space for fresh independent copies.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    staging = local_path(ROOT / 'local' / f'refresh-{stamp}')
    history = local_path(ROOT / 'local/history' / stamp)
    if staging.exists() or history.exists():
        raise RuntimeError('Refresh path already exists.')
    snapshot = staging / 'installed-snapshot'
    dev = staging / 'dev-game'
    old_path = ROOT / 'inventory/snapshot-manifest.json'
    old = json.loads(old_path.read_text()) if old_path.exists() else {'files': []}
    rows = []
    for p in files:
        rel = p.relative_to(source)
        before = digest(p)
        for base in (snapshot, dev):
            dest = base / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
            if digest(dest) != before:
                raise RuntimeError(f'Copied file hash mismatch: {rel}')
        rows.append({'path': rel.as_posix(), 'bytes': p.stat().st_size,
                     'sha256': before, 'in_dev_copy': True})
    if [p.relative_to(source).as_posix() for p in sorted(source.rglob('*')) if p.is_file()] != [r['path'] for r in rows]:
        raise RuntimeError('Installation file set changed during scan; copies not promoted.')
    for row in rows:
        if digest(source / row['path']) != row['sha256']:
            raise RuntimeError(f'Installation changed during scan: {row["path"]}')
    prior = {r['path']: r for r in old['files']}
    current = {r['path']: r for r in rows}
    delta = {'removed': sorted(prior.keys() - current.keys()),
             'added': sorted(current.keys() - prior.keys()),
             'changed': sorted(p for p in prior.keys() & current.keys()
                               if prior[p]['sha256'] != current[p]['sha256']),
             'unchanged': sum(prior[p]['sha256'] == current[p]['sha256'] for p in prior.keys() & current.keys()),
             'comparison_note': 'Prior snapshot excluded installers, RAR backups and dumps; added files may be newly included rather than newly installed.'}
    # Validate all move endpoints before preserving and promoting directory trees.
    moves = []
    for name in ('installed-snapshot', 'dev-game', 'reference'):
        active = local_path(ROOT / 'local' / name)
        archived = local_path(history / name)
        if active.exists():
            moves.append((active, archived))
    for name in ('installed-snapshot', 'dev-game'):
        local_path(staging / name)
        local_path(ROOT / 'local' / name)
    history.mkdir(parents=True)
    if (ROOT / 'inventory').exists():
        shutil.copytree(ROOT / 'inventory', history / 'inventory')
    for active, archived in moves:
        active.rename(archived)
    for name in ('installed-snapshot', 'dev-game'):
        (staging / name).rename(ROOT / 'local' / name)
    staging.rmdir()  # This known staging directory is now empty.
    manifest = {'source': str(source), 'baseline': 'Steam-verified base game + DLC',
                'scanned_at_utc': datetime.now(timezone.utc).isoformat(),
                'steam_evidence': evidence, 'excluded_extras': [], 'files': rows}
    out = ROOT / 'inventory'
    out.mkdir(exist_ok=True)
    (out / 'snapshot-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    with (out / 'installation-files.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, ['path', 'bytes', 'sha256', 'in_dev_copy'])
        w.writeheader(); w.writerows(rows)
    report = {'baseline': manifest['baseline'], 'files': len(rows), 'bytes': size,
              'known_addons_present': known_extras, 'history': str(history),
              'steam_evidence': evidence, 'delta_from_old_snapshot': delta,
              'source_unchanged_during_refresh': True}
    (out / 'baseline-refresh.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'delta_from_old_snapshot'}, indent=2))
    print('Delta counts:', {k: len(v) if isinstance(v, list) else v
                            for k, v in delta.items() if k != 'comparison_note'})


if __name__ == '__main__':
    main()
