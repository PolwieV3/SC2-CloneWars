from pathlib import Path
import hashlib
import json
import shutil
import zipfile

root = Path(__file__).resolve().parents[2]
live = Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
gamedata = live / 'local/dev-game/gamedata'
source = gamedata / 'zzzzzzzzzz_SC2_CloneWars_UnitNames.scd'
target_name = 'a_SC2_CloneWars_UnitNames.scd'
deliverable = root / 'outputs/SPHA-T' / target_name
installed = gamedata / target_name
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

with zipfile.ZipFile(source) as z:
    assert z.testzip() is None
    assert b'SPHA-T' in z.read('loc/us/strings_db.lua')
    research = z.read('mods/DLC1/shadow/lua/sim/Research.lua')
    assert b'SPHA-T' in research and b'Jackhammer' not in research
    development = z.read('uncompiled/mods/DLC1/shadow/lua/sim/Research.lua')
    assert b'SPHA-T' in development and b'Jackhammer' not in development

# The game mounts archives alphabetically. The previous names package loaded
# after the stock localization and research archives yet the stock text won.
# Mount the exact same names payload before those archives as well, covering
# the game's first-match lookup without editing a stock archive or other mod.
shutil.copy2(source, deliverable)
assert deliverable.name.lower() < 'bp.scd'
assert deliverable.name.lower() < 'loc_us.scd'
assert deliverable.name.lower() < 'lua.scd'
assert deliverable.name.lower() < 'z_lua_dlc1.scd'
before = {p.name: sha(p) for p in gamedata.glob('*.scd') if p != installed}
if installed.exists() and sha(installed) != sha(deliverable):
    backup = root / 'work/spha/backups' / ('pre-priority-names-' + sha(installed)[:12])
    backup.mkdir(parents=True, exist_ok=True)
    shutil.copy2(installed, backup / target_name)
shutil.copy2(deliverable, installed)
assert sha(installed) == sha(deliverable)
assert before == {p.name: sha(p) for p in gamedata.glob('*.scd') if p != installed}
report = {
    'revision': 'research-name-priority-test-4',
    'reason': 'Research still showed Jackhammer after the later mounted names override. The same already patched names payload now also mounts before stock archives.',
    'installed': str(installed),
    'sha256': sha(installed),
    'source_sha256': sha(source),
    'stock_archives_changed': False,
    'other_archive_hashes_unchanged': True,
    'runtime': 'Research tooltip needs full restart and live confirmation.'
}
(root / 'outputs/SPHA-T/Research-name-priority.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
(live / 'planning/spha-research-name-priority.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
