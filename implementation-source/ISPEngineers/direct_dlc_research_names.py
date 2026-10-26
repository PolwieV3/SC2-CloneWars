from pathlib import Path
import zipfile,hashlib,json,sys,shutil,re
root=Path(__file__).resolve().parent.parent
project=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
game=(project/'local/dev-game/gamedata').resolve();out=root/'outputs/DLC-Research-Direct-Test';out.mkdir(exist_ok=True)
backups=out/'backups';backups.mkdir(exist_ok=True)
sys.path.insert(0,str(project/'tools'));from rename_unit_text import Chunk
values={b'RESEARCH_NAME_0321':b'SPHA-T',b'RESEARCH_NAME_0322':b'ISP Field Engineer',b'SC2_RESEARCH_INFO_0565':b"Unlock the 'SPHA-T' Experimental Unpacking Cannon.",b'SC2_RESEARCH_INFO_0566':b"Unlock the 'ISP Field Engineer' Mobile Repair and Support Unit."}
research='mods/dlc1/shadow/lua/sim/research.lua';changes=[]
for archive in sorted(game.glob('*.scd')):
    if 'uncompiled' in archive.name.lower():continue
    with zipfile.ZipFile(archive) as z:
        names=[n for n in z.namelist() if n.lower() in [research,'loc/us/strings_db.lua']]
        if not names:continue
        infos=z.infolist();original={i.filename:z.read(i.filename) for i in infos}
    payload=dict(original);edits={}
    for name in names:
        data=original[name]
        if not data.startswith(b'\x1bLua'):
            if name.lower()!=research:continue
            source_edits=[]
            def rewrite_string(match):
                token=match[0];content=token[1:-1]
                for key,replacement in values.items():
                    if content.startswith(b'<LOC '+key+b'>'):
                        quote=token[:1];updated=quote+replacement.replace(b'\\',b'\\\\').replace(quote,b'\\'+quote)+quote
                        source_edits.append({'before':content.decode(),'after':replacement.decode()})
                        return updated
                return token
            new=re.sub(rb"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"",rewrite_string,data)
            if new!=data:payload[name]=new;edits[name]=source_edits
            continue
        assert Chunk(data,lambda s:s).result()==data
        previous=[None]
        def transform(s):
            prior=previous[0];previous[0]=s
            if name.lower()==research:
                for key,replacement in values.items():
                    if s.startswith(b'<LOC '+key+b'>'):return replacement
            elif prior in values:return values[prior]
            return s
        chunk=Chunk(data,transform);new=chunk.result()
        assert Chunk(new,lambda s:s).result()==new
        if new!=data:payload[name]=new;edits[name]=chunk.changes
    if not edits:continue
    oldhash=hashlib.sha256(archive.read_bytes()).hexdigest();backup=backups/(oldhash[:12]+'-'+archive.name)
    if not backup.exists():shutil.copy2(archive,backup)
    staged=out/archive.name
    with zipfile.ZipFile(staged,'w') as z:
        for info in infos:z.writestr(info,payload[info.filename])
    with zipfile.ZipFile(staged) as z:
        assert z.testzip() is None
        assert z.namelist()==list(original)
        for name,data in original.items():
            if name not in edits:assert z.read(name)==data
    assert archive.parent==game and archive.resolve().is_relative_to(game)
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==oldhash
    shutil.copy2(staged,archive)
    changes.append({'archive':archive.name,'before_sha256':oldhash,'after_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'backup':str(backup),'entries':edits,'other_entry_bytes_unchanged':True})
previous_report=out/'installation.json'
if previous_report.exists():
    previous=json.loads(previous_report.read_text())
    changes=previous.get('changes',[])+changes
assert any(c['archive']=='z_lua_dlc1.scd' and any(n.lower()==research for n in c['entries']) for c in changes)
assert any(c['archive']=='lua.scd' and any(n.lower()==research for n in c['entries']) for c in changes)
# Remove only the earlier unsuccessful diagnostic override, preserving it for rollback.
probe=game/'zzzzzzzzzzzzzzzzz_SC2_CloneWars_DLCResearchUI.scd'
if probe.exists():
    assert probe.resolve().parent==game
    destination=backups/('disabled-'+hashlib.sha256(probe.read_bytes()).hexdigest()[:12]+'-'+probe.name)
    if destination.exists():destination=backups/('disabled-current-'+probe.name)
    shutil.move(str(probe),str(destination))
report={'date':'2026-10-26','approach':'Direct DLC shadow research resources patched inside development lua.scd and z_lua_dlc1.scd; all competing installed copies normalized. Four NAME/INFO strings only; LOC tags removed for those four research values. English key values normalized in every installed copy. Failed userInit diagnostic disabled.','changes':changes,'steam_originals_modified':False,'uncompiled_archives_modified':False,'research_costs_unlocks_buffs_unchanged':True,'unit_models_beacon_and_sizes_unchanged':True,'runtime_verified':False,'stop_condition':'One more in-game test. If research labels remain wrong, put research renaming on hold; do not keep adding patches.','rollback':'Close dev game; restore each hash-prefixed backup to its original filename in dev gamedata. The previous diagnostic archive is preserved disabled in backups.'}
(out/'installation.json').write_text(json.dumps(report,indent=2));(project/'planning/dlc-research-direct-test-2026-10-26.json').write_text(json.dumps(report,indent=2))
shutil.copy2(Path(__file__),out/Path(__file__).name)
print(json.dumps({'archives_changed':[c['archive'] for c in changes],'research_entries_changed':sum(any(n.lower()==research for n in c['entries']) for c in changes),'runtime_verified':False,'prior_diagnostic_disabled':not probe.exists(),'steam_originals_modified':False},indent=2))
