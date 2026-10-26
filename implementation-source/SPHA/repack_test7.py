from pathlib import Path
import hashlib
import json
import zipfile

work = Path(__file__).resolve().parent
root = work.parents[1]
out = root / 'outputs/SPHA-T'
archive = out / 'zzzzzz_SC2_CloneWars_SPHA.scd'
backup = work / 'backups/test6-before-unit-local-fix.scd'
backup.parent.mkdir(exist_ok=True)
if not backup.exists():
    backup.write_bytes(archive.read_bytes())
else:
    assert archive.read_bytes() == backup.read_bytes() or b'beam-test-7' in zipfile.ZipFile(archive).read('units/CloneWars/SPHA/SPHA_script.lua')
with zipfile.ZipFile(backup) as source:
    assert source.testzip() is None
    original = {name: source.read(name) for name in source.namelist()}
    assert b'beam-test-6' in original['units/CloneWars/SPHA/SPHA_script.lua']
payload = {name: data for name, data in original.items() if not name.endswith('Deploy_Ability.lua')}
payload['units/CloneWars/SPHA/SPHA_script.lua'] = (work / 'SPHA_script.lua').read_bytes()
assert set(original) - set(payload) == {
    'abilities/Deploy_Ability.lua',
    'mods/DLC1/shadow/abilities/Deploy_Ability.lua',
    'uncompiled/mods/DLC1/shadow/abilities/Deploy_Ability.lua',
}
assert all(original[name] == data for name, data in payload.items() if name != 'units/CloneWars/SPHA/SPHA_script.lua')
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as target:
    for name, data in sorted(payload.items()):
        target.writestr(name, data)
with zipfile.ZipFile(archive) as check:
    assert check.testzip() is None
report = json.loads((out / 'Package-validation.json').read_text(encoding='utf8'))
report['revision'] = 'beam-test-7-unit-local-deploy-watch'
report['sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
report['deployment'] = 'Native DLC Load/Unload ability retained; verified-loaded SPHA unit script enables gun after 1.5 seconds planted and disables when mobile.'
report['runtime'] = 'Not yet verified in game.'
report['installed'] = False
(out / 'Package-validation.json').write_text(json.dumps(report, indent=2), encoding='utf8')
print(report['revision'], report['sha256'], len(payload), 'entries')
