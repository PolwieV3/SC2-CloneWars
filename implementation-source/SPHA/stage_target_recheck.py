from pathlib import Path
import hashlib
import json
import zipfile

work = Path(__file__).resolve().parent
root = work.parents[1]
out = root / 'outputs/SPHA-T'
source = out / 'zzzzzz_SC2_CloneWars_SPHA.scd'
staged = out / 'staged-target-recheck.scd'
with zipfile.ZipFile(source) as archive:
    assert archive.testzip() is None
    payload = {name: archive.read(name) for name in archive.namelist()}
blueprints = [name for name in payload if name.endswith('units/zzzz_clonewars_spha_unit.bp')]
assert len(blueprints) == 4
for name in blueprints:
    data = payload[name]
    assert data.count(b'AlwaysRecheckTarget = false,') == 2
    assert data.count(b'TargetCheckInterval = 0.6,') == 1
    # Only the main laser, never the inherited range helper.
    data = data.replace(b'AlwaysRecheckTarget = false,', b'AlwaysRecheckTarget = true,', 1)
    data = data.replace(b'TargetCheckInterval = 0.6,', b'TargetCheckInterval = 0.2,', 1)
    payload[name] = data
with zipfile.ZipFile(staged, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name, data in sorted(payload.items()):
        archive.writestr(name, data)
with zipfile.ZipFile(staged) as archive:
    assert archive.testzip() is None
    assert set(archive.namelist()) == set(payload)
    assert all(archive.read(name) == data for name, data in payload.items())
record = {
    'revision': 'beam-test-8-target-recheck',
    'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'staged_sha256': hashlib.sha256(staged.read_bytes()).hexdigest(),
    'changed_entries': blueprints,
    'change': 'MainGun target recheck enabled; interval 0.6 to 0.2 seconds',
    'runtime': 'Staged only; line of sight behavior not yet verified in game.',
}
(out / 'Target-recheck-validation.json').write_text(json.dumps(record, indent=2))
print(json.dumps(record, indent=2))
