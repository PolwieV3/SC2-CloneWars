from pathlib import Path
import hashlib, json, shutil, zipfile

root = Path(__file__).resolve().parents[2]
live = Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
gamedata = live / 'local/dev-game/gamedata'
names = gamedata / 'zzzzzzzzzz_SC2_CloneWars_UnitNames.scd'
source_archive = gamedata / 'z_uncompiled_lua_dlc1.scd'
source_path = 'uncompiled/mods/DLC1/shadow/lua/sim/Research.lua'
backup_dir = root / 'work/spha/name-fix-dev-source'
backup_dir.mkdir(parents=True, exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

before = sha(names)
backup = backup_dir / names.name
if not backup.exists():
    shutil.copy2(names, backup)

with zipfile.ZipFile(names) as z:
    infos = z.infolist()
    payload = {i.filename: z.read(i.filename) for i in infos}
with zipfile.ZipFile(source_archive) as z:
    research = z.read(source_path)

old_name = b"<LOC RESEARCH_NAME_0321>Jackhammer"
old_info = b"<LOC SC2_RESEARCH_INFO_0565>Unlock the \\'Jackhammer\\' Experimental Unpacking Cannon."
assert research.count(old_name) == 1
assert research.count(old_info) == 1
research = research.replace(old_name, b'SPHA-T')
research = research.replace(old_info, b"Unlock the \\'SPHA-T\\' Experimental Unpacking Cannon.")
assert b'Jackhammer' not in research
payload[source_path] = research

staged = root / 'outputs/SPHA-T' / names.name
with zipfile.ZipFile(staged, 'w') as z:
    seen = set()
    for info in infos:
        z.writestr(info, payload[info.filename])
        seen.add(info.filename)
    if source_path not in seen:
        z.writestr(source_path, payload[source_path])
with zipfile.ZipFile(staged) as z:
    assert z.testzip() is None
    assert z.read(source_path) == research

shutil.copy2(staged, names)
assert sha(names) == sha(staged)
report = {
    'revision': 'research-dev-source-fix-3',
    'reason': 'The GAR development launch exposes uncompiled DLC research sources; patch the same research title and tooltip there as well as in compiled/localization data.',
    'changed_or_added_path': source_path,
    'before_sha256': before,
    'installed_sha256': sha(names),
    'backup': str(backup),
    'gameplay_fields_changed': False,
    'runtime': 'Requires full game restart.'
}
(root / 'outputs/SPHA-T/Research-name-fix-3.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
(live / 'planning/spha-research-name-fix-3.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
