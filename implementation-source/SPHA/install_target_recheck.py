from pathlib import Path
import datetime
import hashlib
import json
import shutil
import subprocess
import zipfile

work = Path(__file__).resolve().parent
root = work.parents[1]
out = root / 'outputs/SPHA-T'
live = Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
staged = out / 'staged-target-recheck.scd'
target = live / 'local/dev-game/gamedata/zzzzzz_SC2_CloneWars_SPHA.scd'
report_path = out / 'Target-recheck-validation.json'
report = json.loads(report_path.read_text(encoding='utf8'))
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(staged) == report['staged_sha256']
assert digest(target) == report['source_sha256'], 'Live package changed after staging; inspect before installing.'
with zipfile.ZipFile(staged) as archive:
    assert archive.testzip() is None
running = 'SupremeCommander2.exe' in subprocess.run(
    ['tasklist', '/FI', 'IMAGENAME eq SupremeCommander2.exe', '/FO', 'CSV', '/NH'],
    capture_output=True, text=True).stdout
assert not running, 'Close Supreme Commander 2 before installing.'
other_before = {p.name: digest(p) for p in target.parent.glob('*.scd') if p != target}
backup_dir = work / 'backups' / ('pre-test8-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
backup_dir.mkdir(parents=True)
shutil.copy2(target, backup_dir / target.name)
shutil.copy2(staged, target)
assert digest(target) == report['staged_sha256']
other_after = {p.name: digest(p) for p in target.parent.glob('*.scd') if p != target}
assert other_after == other_before
report.update({'installed': True, 'installed_path': str(target), 'backup': str(backup_dir / target.name),
               'other_archives_unchanged': len(other_before), 'runtime': 'Installed; game restart and cliff test required.'})
report_path.write_text(json.dumps(report, indent=2), encoding='utf8')
(live / 'planning/spha-beam-test-8-installation.json').write_text(json.dumps(report, indent=2), encoding='utf8')
print('Installed', report['revision'], report['staged_sha256'], 'other archives unchanged', len(other_before))
