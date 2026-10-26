from pathlib import Path
import hashlib
import json
import shutil
import zipfile

root=Path(__file__).resolve().parents[2]
live=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
gamedata=live/'local/dev-game/gamedata'
out=root/'outputs/SPHA-T'
stock=gamedata/'z_uncompiled_lua_dlc1.scd'
paths=('mods/DLC1/shadow/lua/sim/Research.lua','uncompiled/mods/DLC1/shadow/lua/sim/Research.lua')
with zipfile.ZipFile(stock) as z:
    source=z.read(paths[1])
edits={
    b"<LOC SC2_RESEARCH_INFO_0275>Unlock the \\'AT-RT\\' Assault Bot.":b'<LOC SC2_RESEARCH_INFO_0275>Unlock the AT-RT.',
    b'<LOC RESEARCH_NAME_0321>Jackhammer':b'SPHA-T',
    b"<LOC SC2_RESEARCH_INFO_0565>Unlock the \\'Jackhammer\\' Experimental Unpacking Cannon.":b"Unlock the \\'SPHA-T\\' Experimental Unpacking Cannon.",
}
for old,new in edits.items():
    assert source.count(old)==1,(old,source.count(old))
    source=source.replace(old,new)
assert b'Jackhammer' not in source
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reports=[]
for archive_name in ('a_SC2_CloneWars_UnitNames.scd','zzzzzzzzzz_SC2_CloneWars_UnitNames.scd'):
    installed=gamedata/archive_name
    staged=out/archive_name
    with zipfile.ZipFile(installed) as z:
        infos=z.infolist()
        payload={info.filename:z.read(info.filename) for info in infos}
    assert all(path in payload for path in paths)
    previous=sha(installed)
    backup=root/'work/spha/backups'/('pre-research-source-'+archive_name+'-'+previous[:12])
    backup.mkdir(parents=True,exist_ok=True)
    shutil.copy2(installed,backup/archive_name)
    for path in paths:payload[path]=source
    with zipfile.ZipFile(staged,'w') as z:
        for info in infos:z.writestr(info,payload[info.filename])
    with zipfile.ZipFile(staged) as z:
        assert z.testzip() is None
        assert all(z.read(path)==source for path in paths)
    shutil.copy2(staged,installed)
    assert sha(installed)==sha(staged)
    reports.append({'archive':archive_name,'before_sha256':previous,'after_sha256':sha(installed),'backup':str(backup/archive_name)})
report={'revision':'dlc-research-source-test-5','changed_resource_paths':paths,'text_edits':3,'research_cost_prerequisite_unlock_unchanged':True,'archives':reports,'runtime':'Full restart needed to verify SPHA-T in the DLC research tooltip.'}
(out/'DLC-research-source-installation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(live/'planning/spha-dlc-research-source-installation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
