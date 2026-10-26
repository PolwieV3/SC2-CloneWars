from pathlib import Path
import re,zipfile,hashlib,json,shutil,sys
root=Path(__file__).resolve().parent.parent
project=Path(r'C:/Users/gavad/Documents/Codex/2026-10-03/referenced-chatgpt-conversation-this-is-an/outputs/SC2-CloneWars')
sys.path.insert(0,str(project/'tools'));from rename_unit_text import Chunk
game=project/'local/dev-game/gamedata';out=root/'outputs/ISP-Refinement-4';out.mkdir(exist_ok=True)
name='zzzzzzzzzzzzzzzz_SC2_CloneWars_ISP_Names.scd'
pattern=re.compile(rb'(?<!ISP )\bField Engineer(s)?\b',re.I)
def rename(v):
    if v.startswith((b'/',b'\\',b'\x1bLua')):return v
    v=v.replace(b'ISP Engineer (Test)',b'ISP Engineer').replace(b'ISP Field Engineer (Test)',b'ISP Field Engineer')
    return pattern.sub(lambda m:b'ISP Field Engineer'+(b's' if m[1] else b''),v)
effective={}
for archive in sorted(game.glob('*.scd'),key=lambda p:p.name.lower()):
    if archive.name==name or 'uncompiled' in archive.name.lower():continue
    with zipfile.ZipFile(archive) as z:
        for entry in z.namelist():
            if entry.lower().endswith(('.lua','.bp')) and not entry.lower().startswith('uncompiled/'):
                effective[entry.lower()]=(archive,entry)
payload={};changes=[];opened={}
try:
    for _,(archive,entry) in effective.items():
        if archive not in opened:opened[archive]=zipfile.ZipFile(archive)
        data=opened[archive].read(entry)
        if b'field engineer' not in data.lower() and b'ISP Engineer (Test)' not in data:continue
        if data.startswith(b'\x1bLua'):
            assert Chunk(data,lambda v:v).result()==data
            chunk=Chunk(data,rename);new=chunk.result();detail=chunk.changes
            assert Chunk(new,lambda v:v).result()==new
        else:
            # Source files: apply inside quoted visible strings only, not code identifiers.
            detail=[]
            def replace(m):
                old=m[2];updated=rename(old)
                if updated!=old:detail.append({'before':old.decode(errors='replace'),'after':updated.decode(errors='replace')})
                return m[1]+updated+m[1]
            new=re.sub(rb"(['\"])([^'\"\r\n]*)\1",replace,data)
        if new!=data:
            payload[entry]=new;changes.append({'entry':entry,'source':archive.name,'changes':detail})
finally:
    for z in opened.values():z.close()
assert payload and any(n.lower()=='loc/us/strings_db.lua' for n in payload)
# Every effective localization/text resource containing a bare English name must
# now be replaced or already use the ISP prefix. Bytecode instructions untouched.
for entry,data in payload.items():
    if data.startswith(b'\x1bLua'):
        remaining=[];Chunk(data,lambda v:remaining.append(v) or v).result()
        assert not any(pattern.search(v) for v in remaining if not v.startswith((b'/',b'\\'))),entry
archive=out/name
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for n,b in sorted(payload.items()):z.writestr(n,b)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
target=game/name
if target.exists():
    backup=out/'backups';backup.mkdir(exist_ok=True);shutil.copy2(target,backup/(hashlib.sha256(target.read_bytes()).hexdigest()[:12]+'-'+name))
shutil.copy2(archive,target);assert target.read_bytes()==archive.read_bytes()
report={'date':'2026-10-26','name_mapping':{'uul0002':'ISP Engineer','uul0003d1':'ISP Field Engineer'},'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'installed':str(target),'entries_changed':len(payload),'changes':changes,'lua_instructions_and_numbers_unchanged':True,'runtime_ui_verified':False,'scope':'All effective runtime Lua/blueprint resources containing the English name; research, localization, tooltips and selection text included. Uncompiled source archives untouched.'}
(out/'name-verification.json').write_text(json.dumps(report,indent=2));(project/'planning/isp-names-2026-10-26.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'entries_changed':len(payload),'strings_changed':sum(len(x['changes']) for x in changes),'research_entries':[x['entry'] for x in changes if 'research' in x['entry'].lower()],'localization':[x['entry'] for x in changes if x['entry'].lower().startswith('loc/')],'installed':str(target)},indent=2))
