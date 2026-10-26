from pathlib import Path
import zipfile, hashlib, json, re, shutil
root=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
game=root/'local/dev-game/gamedata'
out=Path('outputs/Name-Correction'); out.mkdir(parents=True,exist_ok=True)
report={'date':'2026-10-26','runtime_verified':False,'mapping':{'uul0102':'AT-AP','uul0103':'AT-RT'},'archives':[]}
for path in sorted(game.glob('*UnitNames.scd')):
    original=path.read_bytes(); oldhash=hashlib.sha256(original).hexdigest()
    with zipfile.ZipFile(path) as z:
        entries=[(i,z.read(i)) for i in z.infolist()]
    updated=[]; changed=[]
    for info,data in entries:
        before=data
        if info.filename.endswith('clonewars_unit_names_unit.bp'):
            text=data.decode()
            for uid,name in report['mapping'].items():
                text=re.sub(r"(?m)^.*BlueprintId = '"+uid+r"'.*$",lambda m: re.sub(r"(DisplayName|UnitName) = '[^']*'",lambda x:x[1]+" = '"+name+"'",m[0]),text)
            data=text.encode()
        if data!=before: changed.append(info.filename)
        updated.append((info,data))
    assert len(changed)==4,changed
    backup=out/'backups'/path.name; backup.parent.mkdir(exist_ok=True)
    if not backup.exists(): backup.write_bytes(original)
    staged=out/path.name
    with zipfile.ZipFile(staged,'w') as z:
        for info,data in updated:z.writestr(info,data)
    with zipfile.ZipFile(staged) as z:
        assert z.testzip() is None
        for (info,old),(_,new) in zip(entries,updated):
            assert z.read(info.filename)==new
            if info.filename not in changed: assert new==old
    assert hashlib.sha256(path.read_bytes()).hexdigest()==oldhash
    shutil.copy2(staged,path)
    assert staged.read_bytes()==path.read_bytes()
    report['archives'].append({'path':str(path),'before_sha256':oldhash,'after_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'changed_entries':changed,'other_entry_bytes_unchanged':True,'backup':str(backup.resolve())})
for src in [root/'implementation-source/UI-and-balance/build_names.py',Path(r'C:/Users/gavad/Documents/Codex/2026-10-18/let/work/names/build_names.py')]:
    text=src.read_text(encoding='utf-8')
    corrected=text.replace("'uul0102':'AT-RT','uul0103':'AT-AP'","'uul0102':'AT-AP','uul0103':'AT-RT'")
    if corrected!=text:
        shutil.copy2(src,out/('original-'+str(len(list(out.glob('original-*'))))+'-build_names.py'))
        src.write_text(corrected,encoding='utf-8')
(out/'verification.json').write_text(json.dumps(report,indent=2))
(root/'planning/unit-name-mapping-fix-2026-10-26.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
