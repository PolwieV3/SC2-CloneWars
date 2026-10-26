from pathlib import Path
import hashlib, json, shutil, zipfile, datetime, subprocess

W = Path(__file__).resolve().parent
R = W.parents[1]
O = R / 'outputs/SPHA-T'
live = Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
src = O / 'zzzzzz_SC2_CloneWars_SPHA.scd'
dst = live / 'local/dev-game/gamedata' / src.name

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

with zipfile.ZipFile(src) as archive:
    assert archive.testzip() is None
report = json.loads((O / 'Package-validation.json').read_text(encoding='utf-8'))
validation = json.loads((O / 'Native-pose-validation.json').read_text(encoding='utf-8'))
assert report['revision'] == 'beam-test-7-unit-local-deploy-watch'
assert report['sha256'] == sha(src)
assert validation['checks'] == 'passed'
with zipfile.ZipFile(src) as package:
    names = set(package.namelist())
    script = package.read('units/CloneWars/SPHA/SPHA_script.lua')
    assert b'beam-test-7' in script and b'self:ForkThread(self.WatchDeployment)' in script
    assert b"SetWeaponEnabledByLabel('MainGun', true)" in script
    assert b"SetWeaponEnabledByLabel('MainGun', false)" in script
    assert not any(name.endswith('Deploy_Ability.lua') for name in names)

running = 'SupremeCommander2.exe' in subprocess.run(
    ['tasklist', '/FI', 'IMAGENAME eq SupremeCommander2.exe', '/FO', 'CSV', '/NH'],
    capture_output=True, text=True).stdout
assert not running, 'Close the isolated game before installing the package'
other_before = {p.name: sha(p) for p in dst.parent.glob('*.scd') if p != dst}
previous = sha(dst) if dst.exists() else None
backup = W / 'backups' / ('pre-test6-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
backup.mkdir(parents=True)
if dst.exists():
    shutil.copy2(dst, backup / dst.name)
old_override = dst.parent / 'a0_SC2_CloneWars_SPHA_Deploy.scd'
if old_override.exists():
    shutil.move(old_override, backup / old_override.name)
    other_before.pop(old_override.name)
shutil.copy2(src, dst)
assert sha(dst) == sha(src)
other_after = {p.name: sha(p) for p in dst.parent.glob('*.scd') if p != dst}
assert other_before == other_after

report.update({
    'installed': True,
    'installed_path': str(dst),
    'installed_sha256_verified': True,
    'previous_sha256': previous,
    'backup': str(backup / dst.name),
    'other_archives_unchanged': other_before,
    'game_was_running_during_install': running,
    'runtime': 'Installed; full restart required. Runtime targeting, beam damage and gait acceptance unverified.',
    'rollback': 'Close the game and restore ' + str(backup / dst.name),
})
(O / 'Package-validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
(live / 'planning/spha-beam-test-7-installation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('Installed', report['revision'], report['sha256'], 'other archives unchanged', len(other_before), 'restart required', running)
